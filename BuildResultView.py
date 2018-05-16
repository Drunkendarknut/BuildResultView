import sublime, sublime_plugin

class BuildResultView(sublime_plugin.EventListener):

    def __init__(self):
        self.in_view = None
        self.out_view = None
        self.last_read = 0
        self.buffer = ""

    def on_query_context(self, view, key, operator, operand, match_all):
        if (key != "BuildResultView"): return

        window = view.window()

        self.last_read = 0;

        self.orig_group = window.active_group()
        self.orig_view = window.active_view()

        sublime.set_timeout(self.move_out_view, 20)

        if self.out_view == None or -1 in window.get_view_index(self.out_view):
            def create_view():
                self.out_view = window.new_file()
                self.out_view.set_name("Build result")
                self.out_view.set_scratch(True)

                if len(self.buffer) > 0:
                    self.out_view.run_command("overwrite_view", {'content': self.buffer})
                    self.buffer = ""

            sublime.set_timeout(create_view, 10)
        else:
            self.out_view.run_command("overwrite_view", {'content': ""})

        self.in_view = window.find_output_panel("exec")
        if self.in_view == None and self.out_view != None:
            self.out_view.run_command("overwrite_view", {'content': "Not ready, try again"})

    def move_out_view(self):
        window = self.out_view.window()
        window.focus_view(self.out_view)

        if window.num_groups() > 1:
            target_group = self.orig_group + 1
            if target_group >= window.num_groups():
                target_group = self.orig_group - 1
            window.set_view_index(self.out_view, target_group, 0)
            window.focus_view(self.orig_view)

    def on_modified(self, view):
        if self.in_view == None or view.id() != self.in_view.id(): return

        begin = self.last_read
        end = view.size()
        content = view.substr(sublime.Region(begin, end))

        if self.out_view == None:
            self.buffer += content
        else:
            if len(self.buffer) > 0:
                content = self.buffer + content
                self.buffer = ""
            self.out_view.run_command("write_view", {'content': content, 'begin': begin, 'end': end})

        self.last_read = end

class WriteView(sublime_plugin.TextCommand):
    def run(self, edit, content, begin, end):
        self.view.replace(edit, sublime.Region(begin, end), content)

class OverwriteView(sublime_plugin.TextCommand):
    def run(self, edit, content):
        self.view.replace(edit, sublime.Region(0, self.view.size()), content)
