; Quick Notification 安装脚本 for Inno Setup
; 版本: 0.1.0

[Setup]
AppId={{8A7C5D2E-1F3B-4A6D-9E8C-7B5F3A2D1E4F}
AppName=Quick Notification
AppVersion=0.1.0
AppVerName=Quick Notification 0.1.0
AppPublisher=Quick Notification
AppPublisherURL=https://github.com/yourusername/quick-notification
AppSupportURL=https://github.com/yourusername/quick-notification
AppUpdatesURL=https://github.com/yourusername/quick-notification
DefaultDirName={localappdata}\Programs\Quick Notification
DefaultGroupName=Quick Notification
AllowNoIcons=yes
OutputDir=..\installer
OutputBaseFilename=QuickNotificationSetup
SetupIconFile=..\assets\quick-notification.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\QuickNotification.exe
UninstallDisplayName=Quick Notification

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\QuickNotification.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Quick Notification"; Filename: "{app}\QuickNotification.exe"
Name: "{group}\{cm:ProgramOnTheWeb,Quick Notification}"; Filename: "https://github.com/yourusername/quick-notification"
Name: "{group}\{cm:UninstallProgram,Quick Notification}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Quick Notification"; Filename: "{app}\QuickNotification.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Quick Notification"; Filename: "{app}\QuickNotification.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\QuickNotification.exe"; Description: "{cm:LaunchProgram,Quick Notification}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Quick Notification"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Quick Notification"; ValueType: string; ValueName: "Version"; ValueData: "0.1.0"

[UninstallDelete]
Type: filesandordirs; Name: "{userdocs}\..\.quick-notification"

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
    ConfigPath := HomePath + '\.quick-notification';
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
