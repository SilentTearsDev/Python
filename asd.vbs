Set ws = CreateObject("WScript.Shell")

' Notepad indítása
ws.Run "notepad.exe"
WScript.Sleep 1000  ' vár 1 másodpercet

' Gépeli a szöveget
ws.SendKeys "Ez automatikusan lett ide irva VBScriptbol..."
ws.SendKeys "{ENTER}"
ws.SendKeys "Mukodik!"
