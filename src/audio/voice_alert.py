"""
语音提示模块
提供语音警报和提示功能
"""
from __future__ import annotations

import subprocess
import platform
import threading
from typing import Optional
from pathlib import Path


class VoiceAlert:
    """语音提示类"""
    
    def __init__(self, enabled: bool = True):
        """
        初始化语音提示
        
        Args:
            enabled: 是否启用语音提示
        """
        self.enabled = enabled
        self.system = platform.system()
        self.lock = threading.Lock()
        
        # 预定义的语音消息
        self.messages = {
            'low_visibility': "光线较暗，请谨慎驾驶",
            'wet_road': "路面湿滑，请注意减速",
            'curve': "前方弯道，请减速慢行",
            'narrow_road': "前方路段狭窄，请注意",
            'ttc_warning': "注意！前方碰撞风险！",
            'obstacle_danger': "危险！前方障碍物！",
            'obstacle_warning': "警告！前方有障碍物"
        }
    
    def speak(self, text: str, lang: str = 'zh-CN'):
        """
        播放语音
        
        Args:
            text: 要播放的文本
            lang: 语言代码（默认中文）
        """
        if not self.enabled:
            return
        
        # 使用线程避免阻塞
        thread = threading.Thread(target=self._speak_thread, args=(text, lang))
        thread.daemon = True
        thread.start()
    
    def _speak_thread(self, text: str, lang: str):
        """语音播放线程"""
        try:
            if self.system == 'Linux':
                # Linux系统使用espeak或festival
                try:
                    subprocess.run(['espeak', '-s', '150', '-v', 'zh', text], 
                                 check=False, timeout=3, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 如果espeak不可用，尝试使用festival
                    try:
                        subprocess.run(['festival', '--tts'], 
                                      input=text.encode('utf-8'),
                                      check=False, timeout=3,
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        print(f"[语音提示] {text}")
            elif self.system == 'Windows':
                # Windows系统使用SAPI
                try:
                    import win32com.client
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(text)
                except ImportError:
                    # 如果没有win32com，使用PowerShell
                    try:
                        ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                        subprocess.run(['powershell', '-Command', ps_command],
                                     check=False, timeout=3,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        print(f"[语音提示] {text}")
            else:
                # macOS或其他系统
                try:
                    subprocess.run(['say', text], check=False, timeout=3,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    print(f"[语音提示] {text}")
        except Exception as e:
            print(f"[语音提示错误] {e}: {text}")
    
    def alert_low_visibility(self):
        """低能见度警报"""
        self.speak(self.messages['low_visibility'])
    
    def alert_wet_road(self):
        """路面湿滑警报"""
        self.speak(self.messages['wet_road'])
    
    def alert_curve(self):
        """弯道警报"""
        self.speak(self.messages['curve'])
    
    def alert_narrow_road(self):
        """狭窄路段警报"""
        self.speak(self.messages['narrow_road'])
    
    def alert_ttc_warning(self, ttc_value: Optional[float] = None):
        """
        TTC紧急警报
        
        Args:
            ttc_value: TTC值（可选）
        """
        message = self.messages['ttc_warning']
        if ttc_value is not None:
            message += f"，预计碰撞时间 {ttc_value:.1f} 秒"
        self.speak(message)
    
    def alert_obstacle_danger(self):
        """障碍物危险警报"""
        self.speak(self.messages['obstacle_danger'])
    
    def alert_obstacle_warning(self):
        """障碍物警告"""
        self.speak(self.messages['obstacle_warning'])
    
    def custom_alert(self, text: str):
        """
        自定义警报
        
        Args:
            text: 自定义文本
        """
        self.speak(text)

