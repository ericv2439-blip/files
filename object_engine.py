#!/usr/bin/env python3
"""Unsupervised image region extraction, similarity clustering, and PNG export.

Install: pip install numpy opencv-python
Run: python object_engine.py --input images --output output
Export: python object_engine.py --output output --export OBJECT_ID

This discovers coherent regions, not guaranteed semantic objects.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def unit_hist(values, bins, ranges):
    hist, _ = np.histogram(values, bins=bins, range=ranges)
    hist = hist.astype(np.float32)
    return (hist / max(float(hist.sum()), 1)).tolist()


def signature(image, mask):
    pixels = image[mask > 0]
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_pixels = hsv[mask > 0]
    color = []
    for channel, upper in [(0, 180), (1, 256), (2, 256)]:
        color.extend(unit_hist(hsv_pixels[:, channel], 12, (0, upper)))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    gradient = np.sqrt(gx * gx + gy * gy)[mask > 0]
    texture = unit_hist(np.clip(gradient, 0, 255), 16, (0, 256))
    ys, xs = np.where(mask > 0)
    x, y, w, h = cv2.boundingRect(mask)
    # Translation- and scale-normalized occupancy grid (retains silhouette shape).
    crop = mask[y:y+h, x:x+w]
    occupancy = (cv2.resize(crop, (16, 16), interpolation=cv2.INTER_AREA) / 255).flatten().tolist()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    perimeter = sum(cv2.arcLength(c, True) for c in contours)
    area = int(len(xs))
    return {
        'color_hist': color, 'texture_hist': texture, 'shape_grid': occupancy,
        'mean_lab': lab[mask > 0].mean(axis=0).round(3).tolist(),
        'area': area, 'bbox': [int(x), int(y), int(w), int(h)],
        'aspect_ratio': round(w / max(h, 1), 5),
        'compactness': round(float(np.clip(4 * np.pi * area / max(perimeter ** 2, 1), 0, 1)), 5),
    }


def similarity(a, b):
    # Each score in [0, 1]; preserve all dimensions rather than just an aggregate.
    ca = np.asarray(a['color_hist']); cb = np.asarray(b['color_hist'])
    ta = np.asarray(a['texture_hist']); tb = np.asarray(b['texture_hist'])
    sa = np.asarray(a['shape_grid']); sb = np.asarray(b['shape_grid'])
    color = float(np.clip(1 - np.abs(ca - cb).sum() / 6, 0, 1))
    texture = float(np.clip(1 - np.abs(ta - tb).sum() / 2, 0, 1))
    shape = float(np.clip(1 - np.abs(sa - sb).mean(), 0, 1))
    geometry = float(np.exp(-abs(np.log(max(a['aspect_ratio'], 1e-5) / max(b['aspect_ratio'], 1e-5)))))
    boundary = float(1 - abs(a['compactness'] - b['compactness']))
    scores = {'color': color, 'texture': texture, 'shape': shape,
              'geometry': geometry, 'boundary': boundary}
    scores['combined'] = round(.25 * color + .15 * texture + .35 * shape + .15 * geometry + .10 * boundary, 6)
    return {k: round(v, 6) for k, v in scores.items()}


def segment(image, min_area=120, spatial_radius=8, color_sigma=22, threshold=0.54):
    """Local affinity edges + graph connected components (no pretrained model).

    Compare Lab colors of adjacent pixels, spatially smooth to estimate local
    consistency, squash affinity with sigmoid, and split on weak connections.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab = cv2.GaussianBlur(lab, (0, 0), 1.0)
    h, w = lab.shape[:2]
    # Downsample large images to keep memory/runtime bounded.
    scale = min(1.0, 850 / max(h, w))
    if scale < 1:
        lab = cv2.resize(lab, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    hh, ww = lab.shape[:2]
    # Horizontal and vertical color dissimilarity, normalized by local context.
    dx = np.linalg.norm(lab[:, 1:] - lab[:, :-1], axis=2)
    dy = np.linalg.norm(lab[1:, :] - lab[:-1, :], axis=2)
    # Local mean color discontinuity is stronger evidence than isolated noise.
    radius = max(1, int(spatial_radius * scale))
    k = 2 * radius + 1
    dx = cv2.blur(dx, (k, k)); dy = cv2.blur(dy, (k, k))
    # sigmoid(sigma - distance), bounded and numerically stable.
    ax = 1 / (1 + np.exp(np.clip((dx - color_sigma) / max(color_sigma * .25, 1), -60, 60)))
    ay = 1 / (1 + np.exp(np.clip((dy - color_sigma) / max(color_sigma * .25, 1), -60, 60)))
    # Union-find connected components of sufficiently strong pixel affinities.
    parent = np.arange(hh * ww, dtype=np.int32)
    size = np.ones(hh * ww, dtype=np.int32)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a = find(a); b = find(b)
        if a == b: return
        if size[a] < size[b]: a, b = b, a
        parent[b] = a; size[a] += size[b]
    # Process strongest connections first; all edges above threshold included.
    for y in range(hh):
        for x in range(ww):
            idx = y * ww + x
            if x + 1 < ww and ax[y, x] >= threshold: union(idx, idx + 1)
            if y + 1 < hh and ay[y, x] >= threshold: union(idx, idx + ww)
    roots = np.array([find(i) for i in range(hh * ww)], dtype=np.int32).reshape(hh, ww)
    unique, counts = np.unique(roots, return_counts=True)
    # Avoid exploding into huge numbers of tiny fragments.
    candidates = unique[counts >= max(4, int(min_area * scale * scale))]
    masks = []
    for root in candidates:
        small = np.uint8(roots == root) * 255
        full = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST) if scale < 1 else small
        if cv2.countNonZero(full) >= min_area:
            masks.append(full)
    return masks


def export_object(db, object_id, out_path):
    obj = next((o for o in db['objects'] if o['id'] == object_id), None)
    if obj is None: raise ValueError(f'Unknown object ID: {object_id}')
    img = cv2.imread(obj['source_image'], cv2.IMREAD_COLOR)
    mask = cv2.imread(obj['mask'], cv2.IMREAD_GRAYSCALE)
    if img is None or mask is None: raise FileNotFoundError('Source image or mask missing')
    if img.shape[:2] != mask.shape: raise ValueError('Image/mask size mismatch')
    x, y, w, h = obj['statistics']['bbox']
    rgba = cv2.cvtColor(img[y:y+h, x:x+w], cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask[y:y+h, x:x+w]
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out_path), rgba): raise IOError(f'Failed to save {out_path}')
    return str(out_path)


def run(args):
    source = Path(args.input); output = Path(args.output)
    masks_dir = output / 'masks'; masks_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(p for p in source.rglob('*') if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.webp'})
    if not paths: raise ValueError(f'No images found in {source}')
    objects, images = [], []
    for path in paths:
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            print('Skipping unreadable image:', path); continue
        image_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:12]
        ids = []
        for index, mask in enumerate(segment(img, args.min_area, args.radius, args.color_sigma, args.affinity_threshold)):
            oid = f'{image_id}_OBJ_{index:05d}'
            mask_path = masks_dir / f'{oid}.png'
            cv2.imwrite(str(mask_path), mask)
            obj = {'id': oid, 'source_image': str(path.resolve()), 'mask': str(mask_path.resolve()),
                   'statistics': signature(img, mask), 'group_id': None}
            objects.append(obj); ids.append(oid)
        images.append({'id': image_id, 'source': str(path.resolve()), 'object_ids': ids,
                       'width': img.shape[1], 'height': img.shape[0]})
        print(f'{path}: {len(ids)} regions')
    # Online representative-based grouping; deterministic but order-dependent.
    groups = []
    for obj in objects:
        best, best_score = None, -1
        for group in groups:
            scores = similarity(obj['statistics'], group['representative'])
            if scores['combined'] > best_score:
                best, best_score = group, scores['combined']
        if best is None or best_score < args.similarity:
            best = {'id': f'PATTERN_{len(groups)+1:05d}', 'representative': obj['statistics'],
                    'members': [], 'frequency': {}}
            groups.append(best)
        best['members'].append(obj['id']); obj['group_id'] = best['id']
        obj['similarity_to_group'] = similarity(obj['statistics'], best['representative'])
    object_lookup = {o['id']: o for o in objects}
    for group in groups:
        group_images = {object_lookup[oid]['source_image'] for oid in group['members']}
        group['frequency'] = {'total_occurrences': len(group['members']),
                              'images_containing': len(group_images),
                              'prevalence': round(len(group_images) / max(len(images), 1), 6),
                              'mean_per_image': round(len(group['members']) / max(len(images), 1), 6)}
    db = {'version': '0.2', 'note': 'Unsupervised visual regions; not validated semantic objects.',
          'images': images, 'objects': objects, 'groups': groups}
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'database.json').open('w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)
    print(f'Saved {len(objects)} regions, {len(groups)} groups to {output / "database.json"}')
    if args.export_first and objects:
        print('Exported:', export_object(db, objects[0]['id'], output / 'objects' / (objects[0]['id'] + '.png')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='images')
    parser.add_argument('--output', default='output')
    parser.add_argument('--min-area', type=int, default=120)
    parser.add_argument('--radius', type=int, default=5)
    parser.add_argument('--color-sigma', type=float, default=18)
    parser.add_argument('--affinity-threshold', type=float, default=.54)
    parser.add_argument('--similarity', type=float, default=.83)
    parser.add_argument('--export', metavar='OBJECT_ID')
    parser.add_argument('--export-first', action='store_true')
    args = parser.parse_args()
    if args.export:
        with (Path(args.output) / 'database.json').open(encoding='utf-8') as f: db = json.load(f)
        print(export_object(db, args.export, Path(args.output) / 'objects' / (args.export + '.png')))
    else: run(args)

if __name__ == '__main__': main()
