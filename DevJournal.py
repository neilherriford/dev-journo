import sublime
import sublime_plugin
from datetime import datetime
import os
import webbrowser
import math
import re

def now_minute(date=False):
    if(date): return datetime.now().strftime("%b %d %H:%M")
    return datetime.now().strftime("%H:%M")

def create_artifact_file_path(root_path, artifact_name):
    artifact_local = datetime.now().strftime("%Y/%W")
    artifact_name = artifact_name.replace(" ", "-")
    artifact_info_file_name = "ℹ️%s-info.markdown" % artifact_name
    artifact_path = os.path.join(root_path, artifact_local, artifact_name)
    if not os.path.exists(artifact_path): os.makedirs(artifact_path)

    return os.path.join(artifact_path, artifact_info_file_name)

def create_project_file_path(root_path, project_name):
    project_local = datetime.now().strftime("%Y/%W")
    project_file_name = "%s.markdown" % project_name
    project_path = os.path.join(root_path, project_local)
    if not os.path.exists(project_path): os.makedirs(project_path)

    return os.path.join(project_path, project_file_name)

def create_meeting_file_path(root_path, meeting_name, start_time):
    now = datetime.now()
    meeting_local = now.strftime("%Y/%W")
    today = now.strftime("%Y%m%d")
    start_time = start_time.replace(":", "")
    meeting_name = meeting_name.replace(" ", "-")
    meeting_file_name = "%s%s📅%s.markdown" % (today, start_time, meeting_name)
    meeting_path = os.path.join(root_path, meeting_local)
    if not os.path.exists(meeting_path): os.makedirs(meeting_path)

    return os.path.join(meeting_path, meeting_file_name)

def create_convo_file_path(root_path, convo_title):
    now = datetime.now()
    meeting_local = now.strftime("%Y/%W")
    today = now.strftime("%Y%m%d")
    start_time = now.strftime("%H%M")
    convo_title = convo_title.replace(" ", "-")
    meeting_file_name = "%s%s💬%s.markdown" % (today, start_time, convo_title)
    meeting_path = os.path.join(root_path, meeting_local)
    if not os.path.exists(meeting_path): os.makedirs(meeting_path)

    return os.path.join(meeting_path, meeting_file_name)

def insert_across_selections(view, edit, contents):
    for region in view.sel():
        if region.empty():
            line = view.line(region)
            view.insert(edit, line.begin(), contents)

def create_log_day_file(root_path):
    project_name = datetime.now().strftime("%Y%m%d")
    project_file_path = create_project_file_path(root_path, project_name)
    return project_file_path

def expand_selector_to_region(view, current_point, selector):
    start_point = current_point
    while start_point > 0 and view.match_selector(start_point - 1 , selector):
        start_point -= 1

    end_point = current_point
    while view.match_selector(end_point, selector):
        end_point += 1

    return sublime.Region(start_point, end_point)

def get_markdown_link(view, current_point):
    INLINE_LINK = "meta.link.inline.markdown"
    LINK_DEFINITION = "markup.underline.link.markdown"
    if not view.match_selector(current_point, INLINE_LINK):
        return None

    while not view.match_selector(current_point, LINK_DEFINITION):
        current_point += 1

    region = expand_selector_to_region(view, current_point, LINK_DEFINITION)

    return view.substr(region)

class WorkLogEntryCommand(sublime_plugin.TextCommand):
    def run(self, edit, entry, root_path):
        seperator = "─"
        line = "%s %s %s\n" % (("► " + now_minute(False)), "".ljust(2, seperator), entry)

        day_log_path = create_log_day_file(root_path)

        found_day_log = False
        view = None
        for window in sublime.windows():
            view = window.find_open_file(day_log_path)
            if view != None:
                break

        # this is super janky -- what if no diary open what if the format is messed up etc
        start = view.line(view.find("^┏ DAY IN REVIEW ╾", 0))
        end = view.line(view.find("╾╼ 𝓕𝓲𝓷 ┛$", start.b))
        view.insert(edit, end.a - 1, line)

class WorkLogEntryPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        self.root_path = root_path
        self.view.window().show_input_panel("Work work:", "", self.run_command, None, None)

    def run_command(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                self.view.run_command("work_log_entry", {"entry": text, "root_path": self.root_path} )
        except ValueError:
            pass


class TimeLineCommand(sublime_plugin.TextCommand):
    def run(self, edit, style="full"):
        seperator = "─"
        if style == "full":
            line = "%s\n" % (seperator + " " + now_minute(True) + " ").ljust(72, seperator)
        elif style == "short":
            line = "%s %s %s " % ("►", now_minute(), "".ljust(2, seperator))
        else:
            line = now
        insert_across_selections(self.view, edit, line)


class SectionPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        self.view.window().show_input_panel("Section title:", "", self.run_command, None, None)

    def run_command(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                active_view.run_command("section", {"caption": text} )
        except ValueError:
            pass


class SectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, caption):
        caption = " %s " % caption
        caption_length = len(caption)

        if caption_length < 72:
            space_width = 72 - caption_length
        else:
            space_width = 0
        left_width = math.floor(space_width / 2.0)
        right_width = space_width - left_width

        line = "%s%s%s\n" % ("".ljust(left_width, "─"), caption, "".rjust(right_width, "─"))
        insert_across_selections(self.view, edit, line)


class LogMeetingPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        self.root_path = root_path
        self.view.window().show_input_panel("Meeting title:", "", self.set_meeting_name, None, None)

    def set_meeting_name(self, text):
        try:
            self.meeting_title = text
            self.view.window().show_input_panel("Start time:", now_minute(), self.run_command, None, None)
        except ValueError:
            pass

    def run_command(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                active_view.run_command("log_meeting", {"meeting_name": self.meeting_title, "root_path": self.root_path, "start_time": text} )
        except ValueError:
            pass


class LogConvoPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        self.root_path = root_path
        self.view.window().show_input_panel("Convo name:", "", self.run_command, None, None)

    def run_command(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                self.view.run_command("log_convo", {"convo_name": text, "root_path": self.root_path} )
        except ValueError:
            pass


class LogMeetingCommand(sublime_plugin.TextCommand):
    def run(self, edit, meeting_name, root_path, start_time):
        meeting_file_path = create_meeting_file_path(root_path, meeting_name, start_time)
        new_file = os.path.exists(meeting_file_path)
        start_time = start_time.strip()
        if len(start_time) == 0:
            start_time = now_minute()
        print("********")
        print(meeting_file_path)
        print("********")
        with open(meeting_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                result = "┏ %s " % meeting_name
                result = result.ljust(71, "━")
                result += """┓
─ 𝑴𝒆𝒕𝒂 ────────

─ 𝑷𝒓𝒆𝒑 ─────────

─ 𝑺𝒖𝒎𝒎𝒂𝒓𝒚 ─────
start: {start}
•
•
•
─ 𝑻𝒐 𝒅𝒐 ───────
🔳
🔳
🔳

─ 𝑺𝒕𝒆𝒂𝒌𝒉𝒐𝒍𝒅𝒆𝒓𝒔 ─

─ 𝑵𝒐𝒕𝒆𝒔 ───────
•
•
•
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 𝓕𝓲𝓷 ━┛
""".format(start=start_time)
                prj.write(result)

        sublime.active_window().open_file(meeting_file_path)


class LogConvoCommand(sublime_plugin.TextCommand):
    def run(self, edit, convo_name, root_path):
        convo_file_path = create_convo_file_path(root_path, convo_name)
        new_file = os.path.exists(convo_file_path)
        start_time = now_minute()
        with open(convo_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                result = "┏ %s " % convo_name
                result = result.ljust(71, "━")
                result += """┓
─ 𝑷𝒓𝒆𝒑 ─────────

─ 𝑺𝒖𝒎𝒎𝒂𝒓𝒚 ─────
start: {start}
•
•
•
─ 𝑻𝒐 𝒅𝒐 ───────
🔳
🔳
🔳

─ 𝑺𝒕𝒆𝒂𝒌𝒉𝒐𝒍𝒅𝒆𝒓𝒔 ─

─ 𝑵𝒐𝒕𝒆𝒔 ───────
•
•
•
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 𝓕𝓲𝓷 ━┛
""".format(start=start_time)
                prj.write(result)

        sublime.active_window().open_file(convo_file_path)


class LogMeetingCommand2(sublime_plugin.TextCommand):
    def run(self, edit, meeting_name):
        result = "┏ %s " % meeting_name
        result = result.ljust(71, "━")
        result += """┓
─ 𝑷𝒓𝒆𝒑 ─────────

─ 𝑺𝒖𝒎𝒎𝒂𝒓𝒚 ─────
start: {start}
•
•
•
─ 𝑻𝒐 𝒅𝒐 ───────
🔳
🔳
🔳

─ 𝑺𝒕𝒆𝒂𝒌𝒉𝒐𝒍𝒅𝒆𝒓𝒔 ─

─ 𝑵𝒐𝒕𝒆𝒔 ───────
•
•
•
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 𝓕𝓲𝓷 ━┛
""".format(start=now_minute())
        insert_across_selections(self.view, edit, result)


class LogTaskPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.window().show_input_panel("Task title:", "", self.on_done, None, None)

    def on_done(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                active_view.run_command("log_task", {"task_name": text} )
        except ValueError:
            pass

class LogTaskCommand(sublime_plugin.TextCommand):
    def run(self, edit, task_name):
        result = "┌ %s " % task_name
        result = result.ljust(67, "─")
        result += """🔳──┐
─ 𝑺𝒖𝒎𝒎𝒂𝒓𝒚 ─────
start: {start}

─ 𝑺𝒕𝒆𝒂𝒌𝒉𝒐𝒍𝒅𝒆𝒓𝒔 ─
•

─ 𝑵𝒐𝒕𝒆𝒔 ───────
•
└─────────────────────────────────────────────────────────────── 𝓕𝓲𝓷 ─┘
""".format(start=now_minute())
        insert_across_selections(self.view, edit, result)

class LogProjectPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        self.root_path = root_path
        self.view.window().show_input_panel("Project name:", "", self.on_done, None, None)

    def on_done(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                active_view.run_command("log_project", {"project_name": text, "root_path": self.root_path})
        except ValueError:
            pass

class LogProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit, project_name, root_path):
        project_file_path = create_project_file_path(root_path, project_name)
        new_file = os.path.exists(project_file_path)

        with open(project_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                project_name_length = len(project_name)
                header = " ┏━"
                header += "".ljust(project_name_length + 1, "━")
                header += "┓\n"
                header += "━┛ %s ┗━" % project_name
                fill = 72 - 6 - project_name_length
                if fill > 0: header += "".ljust(fill, "━")
                header += "\nStart: %s\n" % now_minute(True)
                prj.write(header)

        sublime.active_window().open_file(project_file_path)

class LogArtifactPromptCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        self.root_path = root_path
        self.view.window().show_input_panel("Artifact name:", "", self.on_done, None, None)

    def on_done(self, text):
        try:
            active_view = self.view.window().active_view()
            if active_view:
                active_view.run_command("log_artifact", {"artifact_name": text, "root_path": self.root_path})
        except ValueError:
            pass

class LogArtifactCommand(sublime_plugin.TextCommand):
    def run(self, edit, artifact_name, root_path):
        artifact_file_path = create_artifact_file_path(root_path, artifact_name)
        new_file = os.path.exists(artifact_file_path)

        with open(artifact_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                artifact_name_length = len(artifact_name)
                header = " ┏━"
                header += "".ljust(artifact_name_length + 1, "━")
                header += "┓\n"
                header += "━┛ %s ┗━" % artifact_name
                fill = 72 - 6 - artifact_name_length
                if fill > 0: header += "".ljust(fill, "━")
                header += "\nStart: %s\n" % now_minute(True)
                prj.write(header)

        sublime.active_window().open_file(artifact_file_path)

class LogDayCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        project_file_path = create_log_day_file(root_path)
        new_file = os.path.exists(project_file_path)

        with open(project_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                prj.write("""```
%s
```
┏ DAY IN REVIEW ╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼━┓

          I will focus on ＿＿＿＿＿＿＿＿
        I am grateful for ＿＿＿＿＿＿＿＿
I am willing to let go of ＿＿＿＿＿＿＿＿

─ 𝑮𝒐𝒂𝒍𝒔 ──────────
•

─ 𝑸𝒖𝒆𝒖𝒆 ──────────

─ 𝑪𝒐𝒎𝒑𝒍𝒆𝒕𝒆𝒅 ──────
✔︎ lunch

─ 𝑹𝒆𝒎𝒂𝒊𝒏𝒈 ────────

─ 𝑻𝒐𝒎𝒐𝒓𝒓𝒐𝒘 ───────

─ 𝑻𝒉𝒆𝒎𝒆𝒔 ─────────
•

─ 𝑳𝒆𝒔𝒔𝒐𝒏𝒔 𝒍𝒆𝒂𝒓𝒏𝒆𝒅 ─

─ 𝑳𝒐𝒈 ────────────
► %s ── start

┗╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼ 𝓕𝓲𝓷 ┛

""" % (datetime.now().strftime("%B %d"), now_minute()))

        sublime.active_window().open_file(project_file_path)

class LogWeeklyGoalsCommand(sublime_plugin.TextCommand):
    def run(self, edit, root_path):
        week = datetime.now().strftime("%W")
        year = datetime.now().strftime("%Y")
        project_name = "%s%s🥅goals" % (year, week)
        project_file_path = create_project_file_path(root_path, project_name)
        new_file = os.path.exists(project_file_path)

        with open(project_file_path, "a", encoding="utf-8") as prj:
            if not new_file:
                prj.write("""```
week %s
```
┏ WEEKLY GOALS ╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼━┓

─ 𝑮𝒐𝒂𝒍𝒔 ──────────
🔳 make lunch

─ 𝑪𝒐𝒎𝒑𝒍𝒆𝒕𝒆𝒅 ──────
✔︎ lunch

┗╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼╾╼ 𝓕𝓲𝓷 ┛

""" % (week))

        sublime.active_window().open_file(project_file_path)


class NavigateLinkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        current_point = view.sel()[0].begin()

        link_text = get_markdown_link(view, current_point)

        if re.match("^https?://", link_text):
            webbrowser.open(link_text)
        else:
            found_view = None
            for window in sublime.windows():
                view = window.find_open_file(link_text)
                if view != None:
                    found_view = view
                    break

            if found_view == None:
                sublime.active_window().open_file(link_text)
            else:
                found_view.window().focus_view(found_view)

class HamsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        plugin_settings = sublime.load_settings("DevJournal.sublime-settings")
        print(plugin_settings.get("root_path"))


# 📌
# class LogWeekCommand(sublime_plugin.TextCommand):
#     def run(self, edit, root_path):
#         week_number = datetime.now().strftime("%W")
#         project_name = "%s-review" % week_number
#         project_file_path = create_project_file_path(root_path, project_name)
#         new_file = os.path.exists(project_file_path)
    
#         with open(project_file_path, "a", encoding="utf-8") as prj:
#             if not new_file:
#                 # start_of_week = datetime.datetime.strptime("2021-W01-1", "%Y-W%W-%w")
#                 # end_of_week = datetime.datetime.strptime("2021-W01-1", "%Y-W%W-%w")
#                 # prj.write("""```
# Week %s %s-%s

# ```
# ─ 𝑻𝒉𝒆𝒎𝒆𝒔 ─────────
# •

# ─ 𝑳𝒆𝒔𝒔𝒐𝒏𝒔 𝒍𝒆𝒂𝒓𝒏𝒆𝒅 ─
# •


# """ % (datetime.now().strftime("%B %d"),   ,))

#         sublime.active_window().open_file(project_file_path)

# bracket cmd
# fonty
# apply multiple regexens
#
