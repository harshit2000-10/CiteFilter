; Inno Setup script: wraps dist\CiteFilter (made by build_windows.bat) into CiteFilter-Setup.exe.
; Installs for the current user only, so no administrator password is needed.

[Setup]
AppId={{3C489FBB-9F08-4F5F-928D-A36EDAF0A0A6}
AppName=CiteFilter
AppVersion=1.0.0
AppPublisher=CiteFilter
DefaultDirName={autopf}\CiteFilter
DefaultGroupName=CiteFilter
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=CiteFilter-Setup
SetupIconFile=..\logo\citefilter.ico
UninstallDisplayIcon={app}\CiteFilter.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\CiteFilter\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\CiteFilter"; Filename: "{app}\CiteFilter.exe"
Name: "{autodesktop}\CiteFilter"; Filename: "{app}\CiteFilter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\CiteFilter.exe"; Description: "Start CiteFilter"; Flags: nowait postinstall skipifsilent
