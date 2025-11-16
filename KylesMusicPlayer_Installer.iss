[Setup]
AppName=Kyles Music Player
AppVersion=1.0
DefaultDirName={commonpf32}\KylesMusicPlayer
DefaultGroupName=Kyles Music Player
OutputBaseFilename=KylesMusicPlayer_Installer
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes

; Modern architecture identifiers (fixes your warning)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes

; Uninstaller metadata
UninstallDisplayIcon={app}\KylesMusicPlayer.exe
UninstallDisplayName=Kyles Music Player

[Files]
Source: "dist\KylesMusicPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu icon
Name: "{group}\Kyles Music Player"; Filename: "{app}\KylesMusicPlayer.exe"; IconFilename: "{app}\icon.ico"

; Desktop icon (created only if user checks the box)
Name: "{commondesktop}\Kyles Music Player"; Filename: "{app}\KylesMusicPlayer.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\KylesMusicPlayer.exe"; Description: "Launch Kyles Music Player"; Flags: nowait postinstall skipifsilent

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional Tasks:"
