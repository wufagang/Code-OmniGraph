import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cagr_collector.dynamic_observer.skywalking_client import SkyWalkingClient
from cagr_collector.context_scraper.git_scraper import GitScraper

@patch('cagr_collector.dynamic_observer.skywalking_client.requests.post')
def test_skywalking_client(mock_post):
    mock_post.return_value.json.return_value = {
        "data": {
            "queryBasicTraces": {
                "traces": [
                    {"endpointNames": ["/api/users"], "duration": 120}
                ]
            }
        }
    }
    
    client = SkyWalkingClient(base_url="http://localhost:12800")
    traces = client.get_traces("service_a")
    
    assert len(traces) == 1
    assert traces[0]["duration"] == 120

@patch('cagr_collector.context_scraper.git_scraper.Repo')
def test_git_scraper(mock_repo):
    mock_commit = MagicMock()
    mock_commit.hexsha = "123456"
    mock_commit.message = "Fix bug JIRA-1234"
    mock_commit.author.name = "John Doe"
    
    mock_repo.return_value.iter_commits.return_value = [mock_commit]
    
    scraper = GitScraper(repo_path="/dummy/path")
    commits = scraper.get_commits_with_jira()
    
    assert len(commits) == 1
    assert commits[0].hash == "123456"
    assert "JIRA-1234" in commits[0].message
