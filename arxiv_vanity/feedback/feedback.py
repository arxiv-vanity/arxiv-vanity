import hashlib

from .pygithub import Github


class Feedback(object):

    def __init__(self, github_access_token, repo_name, project_id, column_id):
        self.gh = Github(github_access_token)
        self.repo = self.gh.get_repo(repo_name)
        self.project = self.repo.get_project(project_id)
        self.column = self.project.get_column(column_id)

    def create_issue(self, arxiv_id, text, jpg_data):
        if not text.strip():
            text = 'No description'
        title = text if len(text) <= 50 else text[:50] + '...'
        body = text

        body += '\n\narXiv ID: ' + arxiv_id
        body += '\n\nhttps://www.arxiv-vanity.com/papers/' + arxiv_id + '/'
        body += '\n\nhttp://localhost:8010/html/' + arxiv_id + '/'

        if jpg_data:
            image_path = self.commit_image(jpg_data)
            body += '\n\n![screenshot](%s)' % image_path

        issue = self.repo.create_issue(title, body)
        self.column.create_card_for_issue(issue.id)

        return issue.html_url

    def commit_image(self, jpg_data):
        image_sha1 = hashlib.sha1(jpg_data).hexdigest()
        image_filename = '/images/%s.jpg' % image_sha1
        message = '[issue-bot-commit] Created image: %s' % image_filename
        self.repo.update_file(image_filename, message, jpg_data,
                              sha=image_sha1)
        raw_path = 'https://github.com/andreasjansson/engrafo-issues/raw/master%s' % image_filename
        return raw_path
