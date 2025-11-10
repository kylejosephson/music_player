; ------------------------------------------------------------
; 🧩 Kyle's Music Player Installer Script
; ------------------------------------------------------------
; This Inno Setup script packages your compiled EXE into a
; professional Windows installer with shortcuts and uninstall support.
; ------------------------------------------------------------

[Setup]
AppName=Kyle's Music Player
AppVersion=1.0.0
DefaultDirName={autopf}\Kyle's Music Player
DefaultGroupName=Kyle's Music Player
UninstallDisplayIcon={app}\Kyles_Music_Player.exe
OutputDir=C:\Dev\Music_Player_Folder\installer
OutputBaseFilename=KylesMusicPlayerSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

; (Optional) Require admin rights if you want it to install under Program Files
PrivilegesRequired=admin

[Files]
Source: "C:\Dev\Music_Player_Folder\dist\Kyles_Music_Player.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Dev\Music_Player_Folder\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Kyle's Music Player"; Filename: "{app}\Kyles_Music_Player.exe"; IconFilename: "{app}\icon.ico"
Name: "{userdesktop}\Kyle's Music Player"; Filename: "{app}\Kyles_Music_Player.exe"; IconFilename: "{app}\icon.ico"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\Kyles_Music_Player.exe"; Description: "Launch Kyle's Music Player"; Flags: nowait postinstall skipifsilent
