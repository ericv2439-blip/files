#Requires AutoHotkey v2.0
#SingleInstance Force

; ============================================================
;                    ALT COMMAND PLANE
; ============================================================
;
; NUMBERS       = VOLUME
; LETTERS       = INTERNET / SERVICES
; F-KEYS        = APPLICATIONS / TOOLS
; ARROWS        = MEDIA / VOLUME
; SPACE         = PLAY / PAUSE
; ENTER         = TERMINAL
;
; LEFT ALT = COMMAND LAYER
;
; ============================================================


; ============================================================
; VOLUME
; ============================================================

<!1::SoundSetVolume(10)
<!2::SoundSetVolume(20)
<!3::SoundSetVolume(30)
<!4::SoundSetVolume(40)
<!5::SoundSetVolume(50)
<!6::SoundSetVolume(60)
<!7::SoundSetVolume(70)
<!8::SoundSetVolume(80)
<!9::SoundSetVolume(90)
<!0::SoundSetVolume(100)

; Alt + ` = Toggle mute
<!`::SoundSetMute(-1)

; Alt + Up = Volume +5
<!Up::AdjustVolume(5)

; Alt + Down = Volume -5
<!Down::AdjustVolume(-5)

AdjustVolume(amount)
{
    current := SoundGetVolume()
    newVolume := Max(0, Min(100, current + amount))
    SoundSetVolume(newVolume)
}


; ============================================================
; MEDIA
; ============================================================

; Previous track
<!Left::Send("{Media_Prev}")

; Next track
<!Right::Send("{Media_Next}")

; Play / Pause
<!Space::Send("{Media_Play_Pause}")

; Mute
<!Backspace::SoundSetMute(1)


; ============================================================
; WINDOW CONTROL
; ============================================================

; Window switcher
<!Tab::AltTab

; Show desktop
<!Home::Send("#d")

; Lock computer
<!End::DllCall("LockWorkStation")

; Minimize active window
<!Esc::WinMinimize("A")


; ============================================================
; SYSTEM
; ============================================================

; Windows Terminal
<!Enter::Run("wt.exe")

; Windows Run
<!Insert::Send("#r")

; Task Manager
<!Delete::Run("taskmgr.exe")


; ============================================================
; INTERNET
; ============================================================

<!y::Run("https://www.youtube.com")
<!x::Run("https://x.com")
<!g::Run("https://www.google.com")
<!f::Run("https://www.facebook.com")
<!t::Run("https://www.twitch.tv")
<!p::Run("https://www.perplexity.ai")
<!o::Run("https://chat.openai.com")
<!r::Run("https://www.reddit.com")


; ============================================================
; SOCIAL / COMMUNICATION
; ============================================================

<!d::Run("https://discord.com")
<!w::Run("https://web.whatsapp.com")
<!i::Run("https://www.instagram.com")
<!l::Run("https://www.linkedin.com")


; ============================================================
; MEDIA / ENTERTAINMENT
; ============================================================

<!n::Run("https://www.netflix.com")
<!s::Run("https://open.spotify.com")


; ============================================================
; SERVICES / SHOPPING
; ============================================================

<!m::Run("https://www.google.com/maps")
<!a::Run("https://www.amazon.com")
<!e::Run("https://www.ebay.com")


; ============================================================
; DEVELOPMENT / KNOWLEDGE
; ============================================================

<!h::Run("https://github.com")
<!k::Run("https://stackoverflow.com")
<!v::Run("https://www.wikipedia.org")


; ============================================================
; GOOGLE SERVICES
; ============================================================

<!c::Run("https://drive.google.com")
<!b::Run("https://docs.google.com")
<!q::Run("https://calendar.google.com")


; ============================================================
; APPLICATIONS / TOOLS
; ============================================================

; F1 = Terminal
<!F1::Run("wt.exe")

; F2 = File Explorer
<!F2::Run("explorer.exe")

; F3 = Command Prompt
<!F3::Run("cmd.exe")

; F4 deliberately remains normal Windows Alt+F4

; F5 = Settings
<!F5::Run("ms-settings:")

; F6 = Task Manager
<!F6::Run("taskmgr.exe")

; F7 = Calculator
<!F7::Run("calc.exe")

; F8 = Notepad
<!F8::Run("notepad.exe")

; F9 = Paint
<!F9::Run("mspaint.exe")

; F10 = Control Panel
<!F10::Run("control.exe")

; F11 = Downloads
<!F11::Run(EnvGet("USERPROFILE") . "\Downloads")

; F12 = Desktop
<!F12::Run("explorer.exe shell:desktop")
