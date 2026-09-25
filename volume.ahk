#Requires AutoHotkey v2.0

; ============================================================
; VOLUME CONTROL
; Alt + Number
; ============================================================

!1::SetVolume(10)
!2::SetVolume(20)
!3::SetVolume(30)
!4::SetVolume(40)
!5::SetVolume(50)
!6::SetVolume(60)
!7::SetVolume(70)
!8::SetVolume(80)
!9::SetVolume(90)
!0::SetVolume(100)

SetVolume(percent)
{
    SoundSetVolume(percent)
}