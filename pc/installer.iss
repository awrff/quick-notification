; Quick Message 安装脚本 for Inno Setup
; 版本: 0.1.0

[Setup]
AppId={{8A7C5D2E-1F3B-4A6D-9E8C-7B5F3A2D1E4F}
AppName=Quick Message
AppVersion=0.1.0
AppVerName=Quick Message 0.1.0
AppPublisher=Quick Message
AppPublisherURL=https://github.com/yourusername/quick-message
AppSupportURL=https://github.com/yourusername/quick-message
AppUpdatesURL=https://github.com/yourusername/quick-message
DefaultDirName={localappdata}\Programs\Quick Message
DefaultGroupName=Quick Message
AllowNoIcons=yes
OutputDir=..\installer_output
OutputBaseFilename=QuickMessageSetup
SetupIconFile=..\assets\quick-message.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\QuickMessage.exe
UninstallDisplayName=Quick Message

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\QuickMessage.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Quick Message"; Filename: "{app}\QuickMessage.exe"
Name: "{group}\{cm:ProgramOnTheWeb,Quick Message}"; Filename: "https://github.com/yourusername/quick-message"
Name: "{group}\{cm:UninstallProgram,Quick Message}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Quick Message"; Filename: "{app}\QuickMessage.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Quick Message"; Filename: "{app}\QuickMessage.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\QuickMessage.exe"; Description: "{cm:LaunchProgram,Quick Message}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Quick Message"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Quick Message"; ValueType: string; ValueName: "Version"; ValueData: "0.1.0"

[UninstallDelete]
Type: filesandordirs; Name: "{userdocs}\..\.quick-message"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  HomePath: string;
  ConfigPath: string;
begin
  if CurUninstallStep = usUninstall then
  begin
    HomePath := ExpandConstant('{userdocs}\..');
    ConfigPath := HomePath + '\.quick-message';
    if DirExists(ConfigPath) then
    begin
      DelTree(ConfigPath, True, True, True);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
  end;
end;
