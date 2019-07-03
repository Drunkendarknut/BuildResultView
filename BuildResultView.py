import sublime, sublime_plugin

class BuildResultView(sublime_plugin.EventListener):

    class Context:
        def __init__(self, window, out_view, last_read, buffer):
            self.window = window
            self.out_view = out_view
            self.last_read = last_read
            self.buffer = buffer

    def __init__(self):
        self.context_table = {}

    def on_post_window_command(self, window, command_name, args):
        if command_name != "build": return
        if args != None and args.get('select', False): return

        # Get build result panel and create context if it doesn't exist
        build_panel = window.find_output_panel("exec")
        if build_panel.id() not in self.context_table:
            self.context_table[build_panel.id()] = self.Context(window, None, 0, "")

        context = self.context_table[build_panel.id()]

        context.last_read = 0

        # We save these values now, so that we don't lose them when we create a new output view.
        orig_view = window.active_view()
        orig_group = window.active_group()

        if context.out_view == None or -1 in context.window.get_view_index(context.out_view):
            context.out_view = None

            # Try to find an output view from an earlier session
            for view in context.window.views():
                if view.settings().get("is_build_result_output_view", False):
                    context.out_view = view
                    break

            if context.out_view == None:
                # Create new output view
                new_view = window.new_file()
                new_view.set_name("Build results")
                new_view.set_scratch(True)
                new_view.set_read_only(True)
                new_view.settings().set("is_build_result_output_view", True)
                context.out_view = new_view

        # Copy settings from build build_panel view to output view
        build_panel_settings = build_panel.settings()
        for key in ["result_file_regex",
                    "result_line_regex",
                    "result_base_dir",
                    "word_wrap",
                    "line_numbers",
                    "gutter",
                    "scroll_past_end"]:
            context.out_view.settings().set(key, build_panel_settings.get(key))
        context.out_view.assign_syntax(build_panel_settings.get("syntax"))

        # Move output view if necessary
        if orig_view.id() != context.out_view.id():
            window.focus_view(context.out_view)
            if window.num_groups() > 1:
                target_group = orig_group + 1
                if target_group >= window.num_groups():
                    target_group = orig_group - 1
                window.set_view_index(context.out_view, target_group, 0)
                window.focus_view(orig_view)

        # Clear output view, and fill it with any buffered contents
        context.out_view.run_command("write_to_output_view", {
            'content': context.buffer,
            'begin': 0,
            'end': context.out_view.size()
        })
        context.buffer = ""

    def on_modified(self, modified_view):
        # Check if the modified view is a known build panel
        context = None
        for panel_id in self.context_table:
            if panel_id == modified_view.id():
                context = self.context_table[panel_id]
                break
        if context == None: return

        begin = context.last_read
        end = modified_view.size()
        content = modified_view.substr(sublime.Region(begin, end))

        # If we don't have an output view for some reason, buffer the output until we do
        if context.out_view == None:
            context.buffer += content
        else:
            # If we have buffered content, prepend it
            if len(context.buffer) > 0:
                content = context.buffer + content
                context.buffer = ""
            context.out_view.run_command("write_to_output_view", {
                'content': content,
                'begin': begin,
                'end': end
            })

        context.last_read = end

class WriteToOutputView(sublime_plugin.TextCommand):
    def run(self, edit, content, begin, end):
        self.view.set_read_only(False)
        self.view.replace(edit, sublime.Region(begin, end), content)
        self.view.set_read_only(True)
        self.view.show(end)
