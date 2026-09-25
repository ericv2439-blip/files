#Requires AutoHotkey v2.0

CoordMode "Mouse", "Screen"

; ============================================================
; MOVE TO MONITOR
; ============================================================

MoveToMonitor(n) {
    ; Get monitor count
    count := MonitorGetCount()

    if (n < 1 || n > count) {
        SoundBeep 300, 150
        return
    }

    ; Get monitor work area
    MonitorGetWorkArea(
        n,
        &left,
        &top,
        &right,
        &bottom
    )

    ; Center of monitor
    x := left + ((right - left) // 2)
    y := top + ((bottom - top) // 2)

    ; Force Windows screen coordinates
    DllCall(
        "SetCursorPos",
        "Int", x,
        "Int", y
    )
}


; ============================================================
; HOTKEYS
; ============================================================

^!1::MoveToMonitor(1)
^!2::MoveToMonitor(2)
^!3::MoveToMonitor(3)
^!4::MoveToMonitor(4)
