; === Kyle's Music Player Installer ===
[Setup]
AppName=Kyle's Music Player
AppVersion=1.0
AppPublisher=Kyle Josephson
DefaultDirName={autopf}\KylesMusicPlayer
DefaultGroupName=Kyle's Music Player
UninstallDisplayIcon={app}\Kyles_Music_Player.exe
OutputBaseFilename=KylesMusicPlayer_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

[Files]
; Copy everything from dist to Program Files folder
Source: "C:\Dev\Music_Player_Folder\dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Start Menu & Desktop shortcuts
Name: "{autoprograms}\Kyle's Music Player"; Filename: "{app}\Kyles_Music_Player.exe"
Name: "{autodesktop}\Kyle's Music Player"; Filename: "{app}\Kyles_Music_Player.exe"