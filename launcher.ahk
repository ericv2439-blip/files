#Requires AutoHotkey v2.0
#SingleInstance Force

; ============================================================
; RCTRL COMMAND LAYER
; ============================================================
;
; Hold RIGHT CTRL + another key.
;
; MODES
;   1 = WEB
;   2 = DISCOVERY
;   3 = SOCIAL / BLOGS
;   4 = BUSINESS / ECONOMY
;   5 = COMPLETE AI STACK
;   6 = CUSTOM 1
;   7 = CUSTOM 2
;
; QUICK ACCESS
;   8 = Desktop
;   9 = Documents
;   0 = Downloads
;
; ============================================================


; ============================================================
; PATHS
; ============================================================

UserDir      := EnvGet("USERPROFILE")
DesktopDir   := UserDir "\Desktop"
DocumentsDir := UserDir "\Documents"
DownloadsDir := UserDir "\Downloads"

AndroidDir := "C:\AndroidDev"
ProjectDir := "C:\AndroidDev\project\PCExtension"
PythonDir  := DocumentsDir "\PythonScripts"
AdbPath    := "C:\Users\Usuario\Documents\platform-tools\adb.exe"


; ============================================================
; CURRENT MODE
; ============================================================

global CurrentMode := 1

SetMode(ModeNumber, ModeName)
{
    global CurrentMode

    CurrentMode := ModeNumber

    ToolTip("MODE " ModeNumber " // " ModeName)
    SetTimer(() => ToolTip(), -1200)
}


; ============================================================
; MODE SELECTORS
; ============================================================

RCtrl & 1::SetMode(1, "WEB")
RCtrl & 2::SetMode(2, "DISCOVERY")
RCtrl & 3::SetMode(3, "SOCIAL / BLOGS")
RCtrl & 4::SetMode(4, "BUSINESS / ECONOMY")
RCtrl & 5::SetMode(5, "AI STACK")
RCtrl & 6::SetMode(6, "CUSTOM 1")
RCtrl & 7::SetMode(7, "CUSTOM 2")


; ============================================================
; QUICK ACCESS
; ============================================================

RCtrl & 8::OpenDirectory(DesktopDir)
RCtrl & 9::OpenDirectory(DocumentsDir)
RCtrl & 0::OpenDirectory(DownloadsDir)


; ============================================================
; MODE-AWARE LETTERS
; ============================================================
;
; Every A-Z shortcut goes through the currently selected mode.
;
; Example:
;
;   RCtrl + 1
;   RCtrl + C
;       -> ChatGPT
;
;   RCtrl + 2
;   RCtrl + C
;       -> Perplexity
;
;   RCtrl + 3
;   RCtrl + C
;       -> Discord
;
; ============================================================

RCtrl & a::ModeAction("A")
RCtrl & b::ModeAction("B")
RCtrl & c::ModeAction("C")
RCtrl & d::ModeAction("D")
RCtrl & e::ModeAction("E")
RCtrl & f::ModeAction("F")
RCtrl & g::ModeAction("G")
RCtrl & h::ModeAction("H")
RCtrl & i::ModeAction("I")
RCtrl & j::ModeAction("J")
RCtrl & k::ModeAction("K")
RCtrl & l::ModeAction("L")
RCtrl & m::ModeAction("M")
RCtrl & n::ModeAction("N")
RCtrl & o::ModeAction("O")
RCtrl & p::ModeAction("P")
RCtrl & q::ModeAction("Q")
RCtrl & r::ModeAction("R")
RCtrl & s::ModeAction("S")
RCtrl & t::ModeAction("T")
RCtrl & u::ModeAction("U")
RCtrl & v::ModeAction("V")
RCtrl & w::ModeAction("W")
RCtrl & x::ModeAction("X")
RCtrl & y::ModeAction("Y")
RCtrl & z::ModeAction("Z")


; ============================================================
; PYTHON / DEVELOPMENT
; ============================================================

RCtrl & F1::RunPython("script01.py")
RCtrl & F2::RunPython("script02.py")
RCtrl & F3::RunPython("script03.py")
RCtrl & F4::RunPython("script04.py")
RCtrl & F5::RunPython("script05.py")

RCtrl & F6::RunTerminal()
RCtrl & F7::RunPowerShell()
RCtrl & F8::RunTerminal(ProjectDir)

RCtrl & F9::RunAdb("devices")
RCtrl & F10::RunAdb("shell")
RCtrl & F11::RunAdb("reverse tcp:8765 tcp:8765")
RCtrl & F12::RunAdb("logcat")


; ============================================================
; WINDOW / SYSTEM CONTROLS
; ============================================================

RCtrl & Home::WinMaximize("A")
RCtrl & End::WinMinimize("A")
RCtrl & Delete::WinClose("A")

RCtrl & Tab::Send("!{Tab}")

RCtrl & PrintScreen::Run("ms-screenclip:")

RCtrl & Enter::RunTerminal(ProjectDir)
RCtrl & Backspace::RunTerminal(PythonDir)


; ============================================================
; MEDIA CONTROLS
; ============================================================

RCtrl & Space::Send("{Media_Play_Pause}")
RCtrl & Left::Send("{Media_Prev}")
RCtrl & Right::Send("{Media_Next}")
RCtrl & Up::Send("{Volume_Up}")
RCtrl & Down::Send("{Volume_Down}")


; ============================================================
; MODE ENGINE
; ============================================================

ModeAction(Key)
{
    global CurrentMode

    switch CurrentMode
    {
        case 1:
            WebMode(Key)

        case 2:
            DiscoveryMode(Key)

        case 3:
            SocialMode(Key)

        case 4:
            BusinessMode(Key)

        case 5:
            AIStackMode(Key)

        case 6:
            CustomMode1(Key)

        case 7:
            CustomMode2(Key)
    }
}


; ============================================================
; MODE 1 — WEB
; ============================================================

WebMode(Key)
{
    switch Key
    {
        case "A": Run("https://anilist.co/")
        case "B": Run("https://www.bing.com/")
        case "C": Run("https://chatgpt.com/")
        case "D": Run("https://discord.com/app")
        case "E": Run("https://www.deviantart.com/")
        case "F": Run("https://www.facebook.com/")
        case "G": Run("https://www.google.com/")
        case "H": Run("https://hentaila.tv/")
        case "I": Run("https://www.instagram.com/")
        case "J": Run("https://www.google.com/search?tbm=isch")
        case "K": Run("https://www.crunchyroll.com/")
        case "L": Run("https://www.punishworld.com/")
        case "M": Run("https://maps.google.com/")
        case "N": Run("https://myanimelist.net/")
        case "O": Run("https://stackoverflow.com/")
        case "P": Run("https://www.pixiv.net/")
        case "Q": Run("https://www.quora.com/")
        case "R": Run("https://www.reddit.com/")
        case "S": Run("https://stackoverflow.com/")
        case "T": Run("https://translate.google.com/")
        case "U": Run("https://github.com/")
        case "V": Run("https://www.artstation.com/")
        case "W": Run("https://en.wikipedia.org/")
        case "X": Run("https://x.com/")
        case "Y": Run("https://www.youtube.com/")
        case "Z": Run("https://www.twitch.tv/")
    }
}


; ============================================================
; MODE 2 — DISCOVERY / INTERNET RESEARCH
; ============================================================

DiscoveryMode(Key)
{
    switch Key
    {
        ; AI search / answer engines
        case "A": Run("https://www.perplexity.ai/")
        case "B": Run("https://www.bing.com/")
        case "C": Run("https://chatgpt.com/")
        case "D": Run("https://you.com/")
        case "E": Run("https://www.google.com/search?tbm=nws")
        case "F": Run("https://www.google.com/")

        ; Search / discovery
        case "G": Run("https://www.google.com/")
        case "H": Run("https://news.ycombinator.com/")
        case "I": Run("https://www.google.com/search?tbm=isch")
        case "J": Run("https://www.google.com/search?tbm=vid")
        case "K": Run("https://www.kagi.com/")
        case "L": Run("https://lens.google.com/")
        case "M": Run("https://www.google.com/maps")
        case "N": Run("https://news.google.com/")
        case "O": Run("https://www.google.com/search?tbm=isch")
        case "P": Run("https://www.producthunt.com/")
        case "Q": Run("https://www.quora.com/")
        case "R": Run("https://www.reddit.com/")
        case "S": Run("https://search.brave.com/")
        case "T": Run("https://trends.google.com/")
        case "U": Run("https://www.google.com/search?tbm=isch")
        case "V": Run("https://www.google.com/search?tbm=vid")
        case "W": Run("https://en.wikipedia.org/")
        case "X": Run("https://x.com/")
        case "Y": Run("https://www.youtube.com/")
        case "Z": Run("https://www.google.com/search")

        ; Additional discovery tools
        case "0": Run("https://www.similarweb.com/")
    }
}


; ============================================================
; MODE 3 — SOCIAL / BLOGS / COMMUNITIES
; ============================================================

SocialMode(Key)
{
    switch Key
    {
        ; Social networks
        case "A": Run("https://www.facebook.com/")
        case "B": Run("https://bsky.app/")
        case "C": Run("https://discord.com/app")
        case "D": Run("https://www.deviantart.com/")
        case "E": Run("https://www.facebook.com/")
        case "F": Run("https://www.facebook.com/")
        case "G": Run("https://groups.google.com/")
        case "H": Run("https://news.ycombinator.com/")
        case "I": Run("https://www.instagram.com/")
        case "J": Run("https://www.facebook.com/")
        case "K": Run("https://www.tumblr.com/")
        case "L": Run("https://www.linkedin.com/")
        case "M": Run("https://mastodon.social/")
        case "N": Run("https://www.reddit.com/")
        case "O": Run("https://www.facebook.com/")
        case "P": Run("https://www.patreon.com/")
        case "Q": Run("https://www.quora.com/")
        case "R": Run("https://www.reddit.com/")
        case "S": Run("https://www.snapchat.com/")
        case "T": Run("https://www.tumblr.com/")
        case "U": Run("https://www.youtube.com/")
        case "V": Run("https://www.vimeo.com/")
        case "W": Run("https://www.wordpress.com/")
        case "X": Run("https://x.com/")
        case "Y": Run("https://www.youtube.com/")
        case "Z": Run("https://www.tiktok.com/")
    }
}


; ============================================================
; MODE 4 — BUSINESS / ECONOMY
; ============================================================

BusinessMode(Key)
{
    switch Key
    {
        ; Markets / finance
        case "A": Run("https://finance.yahoo.com/")
        case "B": Run("https://www.bloomberg.com/")
        case "C": Run("https://www.cnbc.com/")
        case "D": Run("https://www.deepl.com/")
        case "E": Run("https://www.economist.com/")
        case "F": Run("https://fred.stlouisfed.org/")
        case "G": Run("https://www.google.com/finance/")
        case "H": Run("https://www.marketwatch.com/")
        case "I": Run("https://www.investing.com/")
        case "J": Run("https://www.linkedin.com/")
        case "K": Run("https://www.crunchbase.com/")
        case "L": Run("https://www.linkedin.com/")
        case "M": Run("https://www.macrotrends.net/")
        case "N": Run("https://www.nasdaq.com/")
        case "O": Run("https://www.oecd.org/")
        case "P": Run("https://www.producthunt.com/")
        case "Q": Run("https://www.sec.gov/edgar")
        case "R": Run("https://www.reuters.com/")
        case "S": Run("https://www.statista.com/")
        case "T": Run("https://tradingeconomics.com/")
        case "U": Run("https://www.ubs.com/")
        case "V": Run("https://www.wsj.com/")
        case "W": Run("https://www.worldbank.org/")
        case "X": Run("https://www.xe.com/")
        case "Y": Run("https://finance.yahoo.com/")
        case "Z": Run("https://www.zillow.com/")
    }
}


; ============================================================
; MODE 5 — COMPLETE AI STACK
; ============================================================

AIStackMode(Key)
{
    switch Key
    {
        ; General AI
        case "A": Run("https://claude.ai/")
        case "B": Run("https://chatgpt.com/")
        case "C": Run("https://claude.ai/")
        case "D": Run("https://chat.deepseek.com/")
        case "E": Run("https://gemini.google.com/")
        case "F": Run("https://huggingface.co/")
        case "G": Run("https://grok.com/")
        case "H": Run("https://huggingface.co/")
        case "I": Run("https://www.perplexity.ai/")
        case "J": Run("https://aistudio.google.com/")
        case "K": Run("https://console.anthropic.com/")
        case "L": Run("https://chat.mistral.ai/")
        case "M": Run("https://mistral.ai/")
        case "N": Run("https://notebooklm.google.com/")
        case "O": Run("https://platform.openai.com/")
        case "P": Run("https://www.perplexity.ai/")
        case "Q": Run("https://qwen.ai/")
        case "R": Run("https://replicate.com/")
        case "S": Run("https://stability.ai/")
        case "T": Run("https://www.together.ai/")
        case "U": Run("https://www.udio.com/")
        case "V": Run("https://v0.dev/")
        case "W": Run("https://windsurf.com/")
        case "X": Run("https://x.com/")
        case "Y": Run("https://www.youtube.com/")
        case "Z": Run("https://www.zotero.org/")
    }
}


; ============================================================
; MODE 6 — CUSTOM 1
; ============================================================
;
; Add your own URLs here.
;
; Example:
;
; Custom1A := "https://example.com"
;
; ============================================================

Custom1A := "https://en.wikipedia.org/"
Custom1B := ""
Custom1C := ""
Custom1D := ""
Custom1E := ""
Custom1F := ""
Custom1G := ""
Custom1H := ""
Custom1I := ""
Custom1J := ""
Custom1K := ""
Custom1L := ""
Custom1M := ""
Custom1N := ""
Custom1O := ""
Custom1P := ""
Custom1Q := ""
Custom1R := ""
Custom1S := ""
Custom1T := ""
Custom1U := ""
Custom1V := ""
Custom1W := ""
Custom1X := ""
Custom1Y := ""
Custom1Z := ""


CustomMode1(Key)
{
    global Custom1A, Custom1B, Custom1C, Custom1D
    global Custom1E, Custom1F, Custom1G, Custom1H
    global Custom1I, Custom1J, Custom1K, Custom1L
    global Custom1M, Custom1N, Custom1O, Custom1P
    global Custom1Q, Custom1R, Custom1S, Custom1T
    global Custom1U, Custom1V, Custom1W, Custom1X
    global Custom1Y, Custom1Z

    URL := GetCustomURL(Key, 1)

    OpenCustom(URL)
}


; ============================================================
; MODE 7 — CUSTOM 2
; ============================================================

Custom2A := ""
Custom2B := ""
Custom2C := ""
Custom2D := ""
Custom2E := ""
Custom2F := ""
Custom2G := ""
Custom2H := ""
Custom2I := ""
Custom2J := ""
Custom2K := ""
Custom2L := ""
Custom2M := ""
Custom2N := ""
Custom2O := ""
Custom2P := ""
Custom2Q := ""
Custom2R := ""
Custom2S := ""
Custom2T := ""
Custom2U := ""
Custom2V := ""
Custom2W := ""
Custom2X := ""
Custom2Y := ""
Custom2Z := ""


CustomMode2(Key)
{
    global Custom2A, Custom2B, Custom2C, Custom2D
    global Custom2E, Custom2F, Custom2G, Custom2H
    global Custom2I, Custom2J, Custom2K, Custom2L
    global Custom2M, Custom2N, Custom2O, Custom2P
    global Custom2Q, Custom2R, Custom2S, Custom2T
    global Custom2U, Custom2V, Custom2W, Custom2X
    global Custom2Y, Custom2Z

    URL := GetCustomURL(Key, 2)

    OpenCustom(URL)
}


; ============================================================
; CUSTOM URL LOOKUP
; ============================================================

GetCustomURL(Key, SetNumber)
{
    if SetNumber = 1
    {
        switch Key
        {
            case "A": return Custom1A
            case "B": return Custom1B
            case "C": return Custom1C
            case "D": return Custom1D
            case "E": return Custom1E
            case "F": return Custom1F
            case "G": return Custom1G
            case "H": return Custom1H
            case "I": return Custom1I
            case "J": return Custom1J
            case "K": return Custom1K
            case "L": return Custom1L
            case "M": return Custom1M
            case "N": return Custom1N
            case "O": return Custom1O
            case "P": return Custom1P
            case "Q": return Custom1Q
            case "R": return Custom1R
            case "S": return Custom1S
            case "T": return Custom1T
            case "U": return Custom1U
            case "V": return Custom1V
            case "W": return Custom1W
            case "X": return Custom1X
            case "Y": return Custom1Y
            case "Z": return Custom1Z
        }
    }

    if SetNumber = 2
    {
        switch Key
        {
            case "A": return Custom2A
            case "B": return Custom2B
            case "C": return Custom2C
            case "D": return Custom2D
            case "E": return Custom2E
            case "F": return Custom2F
            case "G": return Custom2G
            case "H": return Custom2H
            case "I": return Custom2I
            case "J": return Custom2J
            case "K": return Custom2K
            case "L": return Custom2L
            case "M": return Custom2M
            case "N": return Custom2N
            case "O": return Custom2O
            case "P": return Custom2P
            case "Q": return Custom2Q
            case "R": return Custom2R
            case "S": return Custom2S
            case "T": return Custom2T
            case "U": return Custom2U
            case "V": return Custom2V
            case "W": return Custom2W
            case "X": return Custom2X
            case "Y": return Custom2Y
            case "Z": return Custom2Z
        }
    }

    return ""
}


; ============================================================
; CUSTOM URL OPENER
; ============================================================

OpenCustom(URL)
{
    if URL = ""
    {
        ToolTip("CUSTOM SHORTCUT NOT CONFIGURED")
        SetTimer(() => ToolTip(), -1200)
        return
    }

    Run(URL)
}


; ============================================================
; DIRECTORY
; ============================================================

OpenDirectory(Path)
{
    if !DirExist(Path)
    {
        MsgBox(
            "Directory not found:`n`n" Path,
            "RCTRL COMMAND LAYER",
            "Iconx"
        )
        return
    }

    Run('explorer.exe "' Path '"')
}


; ============================================================
; TERMINAL
; ============================================================

RunTerminal(WorkingDir := "")
{
    if WorkingDir != "" && !DirExist(WorkingDir)
    {
        MsgBox(
            "Directory not found:`n`n" WorkingDir,
            "RCTRL COMMAND LAYER",
            "Iconx"
        )
        return
    }

    if WorkingDir = ""
        Run("cmd.exe")
    else
        Run('cmd.exe /k cd /d "' WorkingDir '"')
}


RunPowerShell()
{
    Run("powershell.exe")
}


; ============================================================
; PYTHON
; ============================================================

RunPython(ScriptName)
{
    global PythonDir

    ScriptPath := PythonDir "\" ScriptName

    if !FileExist(ScriptPath)
    {
        MsgBox(
            "Python script not found:`n`n" ScriptPath,
            "RCTRL COMMAND LAYER",
            "Iconx"
        )
        return
    }

    Run('cmd.exe /k python "' ScriptPath '"')
}


; ============================================================
; ADB
; ============================================================

RunAdb(Command)
{
    global AdbPath

    if !FileExist(AdbPath)
    {
        MsgBox(
            "ADB not found:`n`n" AdbPath,
            "RCTRL COMMAND LAYER",
            "Iconx"
        )
        return
    }

    Run('cmd.exe /k "' AdbPath '" ' Command)
}