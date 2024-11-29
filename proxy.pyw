import time
import ctypes
import winreg
import os
import subprocess
import sys

# Определение констант для обновления настроек прокси
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37

# Функция для очистки настроек прокси
def clear_proxy_settings():
    try:
        # Открываем раздел реестра для параметров прокси
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE) as key:
            # Отключаем прокси-сервер
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            # Очищаем поле для адреса прокси
            # winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
        
        # Применяем изменения с помощью Windows API
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
        
        # print("Параметры прокси очищены и обновлены.")
    except Exception as e:
        print(f"Ошибка при очистке прокси: {e}")

def request_admin_access():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    else:
        print("Запрос на повышение прав администратора...")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            print(f"Не удалось запросить права администратора: {e}")
        return False

def create_task():
    script_path = os.path.abspath(__file__)
    task_name = "ClearProxySettings"
    
    # Проверяем, существует ли уже задача
    try:
        subprocess.run(['schtasks', '/query', '/tn', task_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        print("Задача уже существует в планировщике Windows")
        return
    except subprocess.CalledProcessError:
        pass
    
    # Создаем XML для задачи
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <StartBoundary>2023-10-01T00:00:00</StartBoundary>
    </BootTrigger>
    <TimeTrigger>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <Enabled>true</Enabled>
      <StartBoundary>2023-10-01T00:00:00</StartBoundary>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT72H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>pythonw</Command>
      <Arguments>{script_path}</Arguments>
    </Exec>
  </Actions>
</Task>"""

    # Сохраняем XML во временный файл
    xml_path = os.path.join(os.environ['TEMP'], 'task.xml')
    with open(xml_path, 'w', encoding='utf-16') as f:
        f.write(xml)

    try:
        # Создаем задачу в планировщике с повышенными привилегиями
        subprocess.run(['schtasks', '/create', '/tn', task_name, '/xml', xml_path, '/f', '/ru', 'SYSTEM'], check=True, shell=True)
        print("Задача успешно создана в планировщике Windows")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании задачи: {e}")
    finally:
        # Удаляем временный файл
        if os.path.exists(xml_path):
            os.remove(xml_path)

if __name__ == "__main__":
    if request_admin_access():
        create_task()
        clear_proxy_settings()
