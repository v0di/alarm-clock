from datetime import datetime, timedelta
import math
import os
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import BooleanProperty, NumericProperty
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.pagelayout import PageLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


class ClockLayout(FloatLayout):
    """FloatLayout for displaying the clock."""


class ClockTimeBgLayout(FloatLayout):
    """FloatLayout for the first screen, where there are the clock and the time."""


class InputLayout(FloatLayout):
    """FloatLayout for placing the text-input box used for setting an alarm."""


class NoAlarmLabel(Label):
    """Label displayed when there is no alarm set."""
    pass


class SetAlarmLayout(FloatLayout):
    """FloatLayout for displaying the page where the alarms are set."""


class TimeLayout(FloatLayout):
    "FloatLayout for displaying the time."


class TimeWid(Widget):
    """The time display widget."""


class GeneralLayout(PageLayout):
    "PageLayout for the scheduled alarms and for the set alarm pages."
    time = ObjectProperty(datetime.now())

    def __init__(self, **kwargs):
        Clock.schedule_interval(
            self.update_time, 1
        )
        super().__init__(**kwargs)

    def update_time(self, dt):

        self.time = self.time + timedelta(seconds=1)
        return True


class Alarm(Widget):
    """An alarm widget. It is created upon setting an alarm.
    It has a label displaying the time set and a button to cancel it.
    """
    alarm_time = StringProperty()
    sound = ObjectProperty(
        SoundLoader.load(
            os.path.join('alarm-sounds', 'sound1.wav'),
        )
    )
    playing = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.check = Clock.schedule_interval(self.time_check, 1)
        self.sound.loop = True
        super().__init__(**kwargs)

    def to_datetime(self, value):
        time = self.parent.parent.time
        x = datetime.strptime(value, r'%H:%M:%S')
        x = datetime(time.year, time.month, time.day, x.hour, x.minute, x.second)
        return x

    def time_check(self, dt):
        """Check whether the alarm time is equal to the current time"""
        alarm_time_dt = self.to_datetime(self.alarm_time)
        if (self.parent.parent.time >= alarm_time_dt) and (
            not self.playing):
            self.playing = True
            self.sound.play()
            Clock.schedule_once(
                self.remove, 60
            )
            
    def remove(self, *args):
        """Cancel and remove the alarm from the list of set alarms."""
        if self.playing:
            self.sound.stop()
        self.check.cancel()
        self.parent.remove_widget(self)


class AlarmInput(TextInput):
    """The text-input box for setting an alarm."""

    def __init__(self, **kwargs):
        self.h_patt = re.compile(r'^(([0-1][0-9])|(2[0-3]))$')
        self.m_patt = re.compile(r'^([0-5][0-9])$')
        self.s_patt = self.m_patt
        super().__init__(**kwargs)
   
    def clear_text(self):
        """Clear the text inside the text-input box."""
        Clock.schedule_once(
            lambda _: setattr(
                self, 'text', ''
            )
        )

    def add_colon(self):
        """Add a colon after the hour or minute part has been input."""
        Clock.schedule_once(
            lambda _: setattr(
                self, 'text', str(self.text) + ':'
                )
            )

    def move_cursor_colon(self):
        """Move cursor one slot to the right after a colon has been put."""
        Clock.schedule_once(
            lambda _: setattr(
                self, 'cursor', (self.cursor[0]+1, self.cursor[1])
                )
            )

    def keyboard_on_key_down(self, window, keycode, text, modifiers):

        if len(self.text) == 8:
            if keycode[1] == 'enter':
                alarms_lay = self.parent.parent.parent.children[1]
                try:
                    if len(alarms_lay.children) < 5:
                        alarms_lay.add_widget(
                            Alarm(alarm_time=self.text)
                        )
                except IndexError:
                    alarms_lay.add_widget(Alarm(alarm_time=self.text))
                self.clear_text()
                Clock.schedule_once(
                    lambda _: setattr(
                        self, 'focus', False
                    )
                )
            elif keycode[1] == 'backspace':
                self.clear_text()
            Clock.schedule_once(
            lambda _: setattr(
                self, 'text', self.text[:-1]
                )
            )
            return True

        for c in keycode[1]:  # Checks whether the pressed key is a number key.
            if c.isdigit():
                return super().keyboard_on_key_down(window, keycode, text, modifiers)
        self.clear_text()
        return True


    def on_text(self, instance, value):
        """Listen to text changes."""
        length = len(self.text)
        if length == 2:
            if self.h_patt.match(self.text):
                self.add_colon()
                self.move_cursor_colon()
                return True    
            self.clear_text()
            return True

        elif length == 5:
            mins = self.text[-2:]
            if self.m_patt.match(mins):
                self.add_colon()
                self.move_cursor_colon()
                return True
            self.clear_text()
            return True

        elif length == 8:
            secs = self.text[-2:]
            if self.m_patt.match(secs):
                return True
            self.clear_text()
            return True


class AlarmsLayout(BoxLayout):
    """BoxLayout for displaying all the set alarms. Each alarm created
    will stack on top of each other."""
    label = ObjectProperty()

    def __init__(self, **kwargs):
        Clock.schedule_interval(self.check_if_alarms, 0.05)
        super().__init__(**kwargs)

    def check_if_alarms(self, dt):

        if not self.label and not self.children:
            self.label = NoAlarmLabel()
            self.add_widget(self.label)
        elif self.label and len(self.children) > 1:
            self.remove_widget(self.label)
            self.label = ''
                

class ClockWid(Widget):
    """The clock widget."""
    h_degrees = NumericProperty()
    m_degrees = NumericProperty()
    s_degrees = NumericProperty()

    def __init__(self, **kwargs):
        self.clock = Clock.schedule_interval(self.set_degrees, 1)
        super().__init__(**kwargs)
        
    def angle(self, pointer: str):
        """Calculate the degrees of the clock pointers (hours, minutes and seconds)."""
        now = self.parent.parent.parent.time
        if pointer == 'hour':
            segs = (now.hour%12)*60*60 + now.minute*60 + now.second
            return math.radians((360/(12*60*60))*segs)
        elif pointer == 'minute':
            segs = now.minute*60 + now.second
            return math.radians((360/(60*60))*segs)
        elif pointer == 'second':
            return math.radians((360/60)*now.second)

    def set_degrees(self, dt):
        """Set the clock's degrees properties."""
        self.h_degrees = self.angle('hour')
        self.m_degrees = self.angle('minute')
        self.s_degrees = self.angle('second')
        return True


class AlarmClockApp(App):
    """The main application."""
    def build(self):
        return GeneralLayout()


if __name__ == '__main__':
    AlarmClockApp().run()
