import github

# until projects make it into pygithub
class MonkeyPatchedRepo(github.Repository.Repository):

    def get_projects(self):
        return github.PaginatedList.PaginatedList(
            GitHubProject,
            self._requester,
            self.url + '/projects',
            None,
            headers = {
                'Accept': 'application/vnd.github.inertia-preview+json'
            },
        )

    def get_project(self, id):
        assert isinstance(id, int), id
        url = '%s/projects/%d' % (
                github.MainClass.DEFAULT_BASE_URL, id)
        headers, data = self._requester.requestJsonAndCheck(
            'GET',
            url,
            headers = {
                'Accept': 'application/vnd.github.inertia-preview+json'
            },
        )
        return GitHubProject(self._requester, headers, data, completed=True)


class GitHubProject(github.GithubObject.CompletableGithubObject):

    def __repr__(self):
        return self.get__repr__({"id": self._id.value, "name": self._name.value})

    @property
    def owner_url(self):
        self._completeIfNotSet(self._owner_url)
        return self._owner_url.value

    @property
    def url(self):
        self._completeIfNotSet(self._url)
        return self._url.value

    @property
    def html_url(self):
        self._completeIfNotSet(self._html_url)
        return self._html_url.value

    @property
    def columns_url(self):
        self._completeIfNotSet(self._columns_url)
        return self._columns_url.value

    @property
    def id(self):
        self._completeIfNotSet(self._id)
        return self._id.value

    @property
    def name(self):
        self._completeIfNotSet(self._name)
        return self._name.value

    @property
    def body(self):
        self._completeIfNotSet(self._body)
        return self._body.value

    @property
    def number(self):
        self._completeIfNotSet(self._number)
        return self._number.value

    @property
    def state(self):
        self._completeIfNotSet(self._state)
        return self._state.value

    @property
    def creator(self):
        self._completeIfNotSet(self._creator)
        return self._creator.value

    @property
    def created_at(self):
        self._completeIfNotSet(self._created_at)
        return self._created_at.value

    @property
    def updated_at(self):
        self._completeIfNotSet(self._updated_at)
        return self._updated_at.value

    def get_columns(self):
        return github.PaginatedList.PaginatedList(
            GitHubProjectColumn,
            self._requester,
            self.url + '/columns',
            None,
            headers = {
                'Accept': 'application/vnd.github.inertia-preview+json'
            },
        )

    def get_column(self, id):
        url = '%s/projects/columns/%d' % (
                github.MainClass.DEFAULT_BASE_URL, id)
        headers, data = self._requester.requestJsonAndCheck(
            'GET',
            url,
            headers = {
                'Accept': 'application/vnd.github.inertia-preview+json'
            },
        )
        return GitHubProjectColumn(self._requester, headers, data, completed=True)

    def _initAttributes(self):
        self._owner_url = github.GithubObject.NotSet
        self._url = github.GithubObject.NotSet
        self._html_url = github.GithubObject.NotSet
        self._columns_url = github.GithubObject.NotSet
        self._id = github.GithubObject.NotSet
        self._name = github.GithubObject.NotSet
        self._body = github.GithubObject.NotSet
        self._number = github.GithubObject.NotSet
        self._state = github.GithubObject.NotSet
        self._creator = github.GithubObject.NotSet
        self._created_at = github.GithubObject.NotSet
        self._updated_at = github.GithubObject.NotSet

    def _useAttributes(self, attributes):
        if 'owner_url' in attributes:
            self._owner_url = self._makeStringAttribute(attributes['owner_url'])
        if 'url' in attributes:
            self._url = self._makeStringAttribute(attributes['url'])
        if 'html_url' in attributes:
            self._html_url = self._makeStringAttribute(attributes['html_url'])
        if 'columns_url' in attributes:
            self._columns_url = self._makeStringAttribute(attributes['columns_url'])
        if 'id' in attributes:
            self._id = self._makeIntAttribute(attributes['id'])
        if 'name' in attributes:
            self._name = self._makeStringAttribute(attributes['name'])
        if 'body' in attributes:
            self._body = self._makeStringAttribute(attributes['body'])
        if 'number' in attributes:
            self._number = self._makeIntAttribute(attributes['number'])
        if 'state' in attributes:
            self._state = self._makeStringAttribute(attributes['state'])
        if 'creator' in attributes:
            self._creator = self._makeClassAttribute(github.NamedUser.NamedUser, attributes['creator'])
        if 'created_at' in attributes:
            self._created_at = self._makeDatetimeAttribute(attributes['created_at'])
        if 'updated_at' in attributes:
            self._updated_at = self._makeDatetimeAttribute(attributes['updated_at'])


class GitHubProjectColumn(github.GithubObject.CompletableGithubObject):

    def __repr__(self):
        return self.get__repr__({"id": self._id.value, "name": self._name.value})

    @property
    def id(self):
        self._completeIfNotSet(self._id)
        return self._id.value

    @property
    def name(self):
        self._completeIfNotSet(self._name)
        return self._name.value

    @property
    def url(self):
        self._completeIfNotSet(self._url)
        return self._url.value

    @property
    def project_url(self):
        self._completeIfNotSet(self._project_url)
        return self._project_url.value

    @property
    def cards_url(self):
        self._completeIfNotSet(self._cards_url)
        return self._cards_url.value

    @property
    def created_at(self):
        self._completeIfNotSet(self._created_at)
        return self._created_at.value

    @property
    def updated_at(self):
        self._completeIfNotSet(self._updated_at)
        return self._updated_at.value

    def create_card_for_issue(self, issue_id):
        assert isinstance(issue_id, int), issue_id
        post_parameters = {
            'content_id': issue_id,
            'content_type': 'Issue',
        }
        url = '%s/projects/columns/%d/cards' % (
                github.MainClass.DEFAULT_BASE_URL, self.id)
        headers, data = self._requester.requestJsonAndCheck(
            'POST',
            self.url + '/cards',
            input=post_parameters,
            headers = {
                'Accept': 'application/vnd.github.inertia-preview+json'
            },
        )

    def _initAttributes(self):
        self._id = github.GithubObject.NotSet
        self._name = github.GithubObject.NotSet
        self._url = github.GithubObject.NotSet
        self._project_url = github.GithubObject.NotSet
        self._cards_url = github.GithubObject.NotSet
        self._created_at = github.GithubObject.NotSet
        self._updated_at = github.GithubObject.NotSet

    def _useAttributes(self, attributes):
        if 'id' in attributes:
            self._id = self._makeIntAttribute(attributes['id'])
        if 'name' in attributes:
            self._name = self._makeStringAttribute(attributes['name'])
        if 'url' in attributes:
            self._url = self._makeStringAttribute(attributes['url'])
        if 'project_url' in attributes:
            self._project_url = self._makeStringAttribute(attributes['project_url'])
        if 'cards_url' in attributes:
            self._cards_url = self._makeStringAttribute(attributes['cards_url'])
        if 'created_at' in attributes:
            self._created_at = self._makeDatetimeAttribute(attributes['created_at'])
        if 'updated_at' in attributes:
            self._updated_at = self._makeDatetimeAttribute(attributes['updated_at'])


github.Repository.Repository = MonkeyPatchedRepo

from github import *
