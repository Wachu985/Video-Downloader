; Inno Setup script for the Video Downloader Windows installer.
; Compiled in CI with:
;   ISCC.exe /DAppExe=<exe name> /DAppVersion=<x.y.z> installer.iss
; AppExe is detected dynamically because flet names the executable
; after the project slug.

#ifndef AppExe
  #define AppExe "video_downloader.exe"
#endif
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Video Downloader"
#define AppPublisher "wachu985"

[Setup]
AppId=com.wachu985.videodownloader
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\..\build
OutputBaseFilename=VideoDownloader-windows-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExe}
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\build\windows\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
