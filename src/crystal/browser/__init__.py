from crystal.browser.addgroup import AddGroupDialog
from crystal.browser.addrooturl import AddRootUrlDialog
from crystal.browser.entitytree import EntityTree
from crystal.browser.tasktree import TaskTree
from crystal.model import Project, Resource, ResourceGroup, RootResource
from crystal.progress import OpenProjectProgressListener
from crystal.task import RootTask
from crystal.ui.BetterMessageDialog import BetterMessageDialog
import wx

_WINDOW_INNER_PADDING = 10

class MainWindow(object):
    entity_tree: EntityTree
    
    def __init__(self, project: Project, progress_listener: OpenProjectProgressListener) -> None:
        self.project = project
        
        frame = wx.Frame(None, title=project.title)
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame.SetSizer(frame_sizer)
        
        splitter = wx.SplitterWindow(frame, style=wx.SP_LIVE_UPDATE)
        splitter.SetSashGravity(1.0)
        splitter.SetMinimumPaneSize(20)
        
        entity_pane = self._create_entity_pane(splitter, progress_listener)
        task_pane = self._create_task_pane(splitter)
        splitter.SplitHorizontally(entity_pane, task_pane, -task_pane.GetBestSize().height)
        
        frame_sizer.Add(splitter, proportion=1, flag=wx.EXPAND)
        
        frame.Fit()
        frame.Show(True)
        
        self.frame = frame
    
    # === Entity Pane: Init ===
    
    def _create_entity_pane(self, parent, progress_listener: OpenProjectProgressListener):
        pane = wx.Panel(parent)
        pane_sizer = wx.BoxSizer(wx.VERTICAL)
        pane.SetSizer(pane_sizer)
        
        pane_sizer.Add(
            self._create_entity_pane_content(pane, progress_listener),
            proportion=1,
            flag=wx.EXPAND|wx.ALL,
            border=_WINDOW_INNER_PADDING)
        
        return pane
    
    def _create_entity_pane_content(self, parent, progress_listener: OpenProjectProgressListener):
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        content_sizer.Add(
            self._create_entity_tree(parent, progress_listener),
            proportion=1,
            flag=wx.EXPAND)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING)
        content_sizer.Add(self._create_button_bar(parent), flag=wx.EXPAND)
        return content_sizer
    
    def _create_entity_tree(self, parent, progress_listener: OpenProjectProgressListener):
        self.entity_tree = EntityTree(parent, self.project, progress_listener)
        self.entity_tree.peer.Bind(wx.EVT_TREE_SEL_CHANGED, self._on_selected_entity_changed)
        
        return self.entity_tree.peer
    
    def _create_button_bar(self, parent):
        add_url_button = wx.Button(parent, label='+ URL')
        add_url_button.Bind(wx.EVT_BUTTON, self._on_add_url)
        
        add_group_button = wx.Button(parent, label='+ Group')
        add_group_button.Bind(wx.EVT_BUTTON, self._on_add_group)
        
        self._remove_entity_button = wx.Button(parent, label='-')
        self._remove_entity_button.Bind(wx.EVT_BUTTON, self._on_remove_entity)
        self._remove_entity_button.Disable()
        
        self._download_button = wx.Button(parent, label='Download')
        self._download_button.Bind(wx.EVT_BUTTON, self._on_download_entity)
        self._download_button.Disable()
        
        self._update_membership_button = wx.Button(parent, label='Update Membership')
        self._update_membership_button.Bind(wx.EVT_BUTTON, self._on_update_group_membership)
        self._update_membership_button.Disable()
        
        self._view_button = wx.Button(parent, label='View')
        self._view_button.Bind(wx.EVT_BUTTON, self._on_view_entity)
        self._view_button.Disable()
        
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(add_url_button)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING)
        content_sizer.Add(add_group_button)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING)
        content_sizer.Add(self._remove_entity_button)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING * 2)
        content_sizer.AddStretchSpacer()
        content_sizer.Add(self._download_button)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING)
        content_sizer.Add(self._update_membership_button)
        content_sizer.AddSpacer(_WINDOW_INNER_PADDING)
        content_sizer.Add(self._view_button)
        return content_sizer
    
    # === Entity Pane: Properties ===
    
    @property
    def _selection_initial_url(self):
        selected_entity = self.entity_tree.selected_entity
        if type(selected_entity) in (Resource, RootResource):
            return selected_entity.resource.url
        elif type(selected_entity) is ResourceGroup:
            return selected_entity.url_pattern
        else:
            return self.project.default_url_prefix
    
    @property
    def _selection_initial_source(self):
        selected_entity = self.entity_tree.selected_entity
        if type(selected_entity) in (Resource, RootResource):
            parent_of_selected_entity = self.entity_tree.parent_of_selected_entity
            if type(parent_of_selected_entity) in (ResourceGroup, RootResource):
                return parent_of_selected_entity
            else:
                return None
        elif type(selected_entity) is ResourceGroup:
            return selected_entity.source
        else:
            return None
    
    # === Entity Pane: Events ===
    
    def _on_add_url(self, event):
        AddRootUrlDialog(
            self.frame, self._on_add_url_dialog_ok,
            initial_url=self._selection_initial_url)
    
    def _on_add_url_dialog_ok(self, name, url):
        # TODO: Validate user input:
        #       * Is name or url empty?
        #       * Is name or url already taken?
        RootResource(self.project, name, Resource(self.project, url))
        self.entity_tree.update()
    
    def _on_add_group(self, event):
        AddGroupDialog(
            self.frame, self._on_add_group_dialog_ok,
            self.project,
            initial_url=self._selection_initial_url,
            initial_source=self._selection_initial_source)
    
    def _on_add_group_dialog_ok(self, name, url_pattern, source):
        # TODO: Validate user input:
        #       * Is name or url_pattern empty?
        #       * Is name or url_pattern already taken?
        rg = ResourceGroup(self.project, name, url_pattern)
        rg.source = source
        self.entity_tree.update()
    
    def _on_remove_entity(self, event):
        self.entity_tree.selected_entity.delete()
        self.entity_tree.update()
    
    def _on_download_entity(self, event) -> None:
        selected_entity = self.entity_tree.selected_entity
        assert selected_entity is not None
        if self._alert_if_not_downloadable(selected_entity):
            return
        selected_entity.download(needs_result=False)
    
    def _on_update_group_membership(self, event):
        selected_entity = self.entity_tree.selected_entity
        if self._alert_if_not_downloadable(selected_entity):
            return
        selected_entity.update_membership()
    
    def _alert_if_not_downloadable(self, entity):
        """
        Displays an alert if the entity is a group without a source,
        which cannot be downloaded. Returns True if an alert was displayed.
        """
        if type(entity) is ResourceGroup and entity.source is None:
            # TODO: Would be great if we automatically gave the user the option
            #       to select a source for the group. Perhaps by automatically
            #       forwarding the user to the edit dialog for the group.
            dialog = BetterMessageDialog(self.frame,
                message=('The group "%s" does not have a source defined, which ' +
                    'prevents it from being downloaded.') % entity.name,
                title='No Source Defined',
                style=wx.OK)
            dialog.ShowModal()
            dialog.Destroy()
            return True
        else:
            return False
    
    def _on_view_entity(self, event):
        import crystal.server
        import webbrowser
        
        # TODO: If the server couldn't be started (ex: due to the default port being in
        #       use), report an appropriate error.
        self.project.start_server()
        
        archive_url = self.entity_tree.selected_entity.resource.url
        request_url = crystal.server.get_request_url(archive_url)
        webbrowser.open(request_url)
    
    def _on_selected_entity_changed(self, event):
        selected_entity = self.entity_tree.selected_entity
        self._remove_entity_button.Enable(
            type(selected_entity) in (ResourceGroup, RootResource))
        self._download_button.Enable(
            selected_entity is not None)
        self._update_membership_button.Enable(
            type(selected_entity) is ResourceGroup)
        self._view_button.Enable(
            type(selected_entity) in (Resource, RootResource))
    
    # === Task Pane: Init ===
    
    def _create_task_pane(self, parent):
        pane = wx.Panel(parent)
        pane_sizer = wx.BoxSizer(wx.VERTICAL)
        pane.SetSizer(pane_sizer)
        
        pane_sizer.Add(self._create_task_pane_content(pane), proportion=1, flag=wx.EXPAND|wx.ALL, border=_WINDOW_INNER_PADDING)
        
        return pane
    
    def _create_task_pane_content(self, parent):
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        content_sizer.Add(self._create_task_tree(parent), proportion=1, flag=wx.EXPAND)
        return content_sizer
    
    def _create_task_tree(self, parent):
        self.task_tree = TaskTree(parent, self.project.root_task)
        
        return self.task_tree.peer
