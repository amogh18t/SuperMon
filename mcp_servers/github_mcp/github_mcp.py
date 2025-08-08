"""GitHub MCP Server for SuperMon platform."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import github3

logger = logging.getLogger(__name__)


class GitHubIssue(BaseModel):
    """GitHub issue model."""
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue description")
    labels: Optional[List[str]] = Field(None, description="Issue labels")
    assignees: Optional[List[str]] = Field(None, description="Issue assignees")
    milestone: Optional[str] = Field(None, description="Milestone name")


class GitHubPR(BaseModel):
    """GitHub pull request model."""
    title: str = Field(..., description="PR title")
    body: str = Field(..., description="PR description")
    head: str = Field(..., description="Source branch")
    base: str = Field(..., description="Target branch")
    labels: Optional[List[str]] = Field(None, description="PR labels")
    assignees: Optional[List[str]] = Field(None, description="PR assignees")


class GitHubRepository(BaseModel):
    """GitHub repository model."""
    name: str = Field(..., description="Repository name")
    description: Optional[str] = Field(None, description="Repository description")
    private: bool = Field(False, description="Is private repository")
    auto_init: bool = Field(True, description="Initialize with README")
    gitignore_template: Optional[str] = Field(None, description="Gitignore template")
    license_template: Optional[str] = Field(None, description="License template")


class GitHubBranch(BaseModel):
    """GitHub branch model."""
    name: str = Field(..., description="Branch name")
    source_branch: Optional[str] = Field(None, description="Source branch for new branch")
    protection_rules: Optional[Dict[str, Any]] = Field(None, description="Branch protection rules")


class GitHubMCPResponse(BaseModel):
    """Standard MCP response model."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class GitHubMCPServer:
    """GitHub MCP Server implementation."""
    
    def __init__(self):
        """Initialize GitHub MCP Server."""
        self.app = FastAPI(title="GitHub MCP Server", version="1.0.0")
        self.client: Optional[github3.GitHub] = None
        self.api_token: Optional[str] = None
        self.repositories_cache: Dict[str, Dict[str, Any]] = {}
        self.issues_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.prs_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize GitHub client on startup."""
            await self._initialize_client()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown."""
            await self._cleanup()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "GitHub MCP Server",
                "connected": self.client is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/create-repository")
        async def create_repository(repo: GitHubRepository):
            """Create a new GitHub repository."""
            try:
                result = await self._create_repository(repo)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating repository: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/repositories")
        async def get_repositories():
            """Get all repositories."""
            try:
                result = await self._get_repositories()
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting repositories: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-issue/{owner}/{repo}")
        async def create_issue(owner: str, repo: str, issue: GitHubIssue):
            """Create a new GitHub issue."""
            try:
                result = await self._create_issue(owner, repo, issue)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating issue: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/issues/{owner}/{repo}")
        async def get_issues(owner: str, repo: str, state: str = "open"):
            """Get issues from a repository."""
            try:
                result = await self._get_issues(owner, repo, state)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting issues: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-pr/{owner}/{repo}")
        async def create_pr(owner: str, repo: str, pr: GitHubPR):
            """Create a new GitHub pull request."""
            try:
                result = await self._create_pr(owner, repo, pr)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating PR: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/pull-requests/{owner}/{repo}")
        async def get_pull_requests(owner: str, repo: str, state: str = "open"):
            """Get pull requests from a repository."""
            try:
                result = await self._get_pull_requests(owner, repo, state)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting PRs: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-branch/{owner}/{repo}")
        async def create_branch(owner: str, repo: str, branch: GitHubBranch):
            """Create a new branch."""
            try:
                result = await self._create_branch(owner, repo, branch)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating branch: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/branches/{owner}/{repo}")
        async def get_branches(owner: str, repo: str):
            """Get branches from a repository."""
            try:
                result = await self._get_branches(owner, repo)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting branches: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/create-file/{owner}/{repo}")
        async def create_file(
            owner: str,
            repo: str,
            path: str,
            content: str,
            message: str,
            branch: str = "main"
        ):
            """Create a new file in a repository."""
            try:
                result = await self._create_file(owner, repo, path, content, message, branch)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error creating file: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.get("/workflows/{owner}/{repo}")
        async def get_workflows(owner: str, repo: str):
            """Get GitHub Actions workflows."""
            try:
                result = await self._get_workflows(owner, repo)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error getting workflows: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        @self.app.post("/trigger-workflow/{owner}/{repo}")
        async def trigger_workflow(
            owner: str,
            repo: str,
            workflow_id: str,
            ref: str = "main"
        ):
            """Trigger a GitHub Actions workflow."""
            try:
                result = await self._trigger_workflow(owner, repo, workflow_id, ref)
                return GitHubMCPResponse(
                    success=True,
                    data=result,
                    timestamp=datetime.utcnow()
                )
            except Exception as e:
                logger.error(f"Error triggering workflow: {e}")
                return GitHubMCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
    
    async def _initialize_client(self):
        """Initialize GitHub client."""
        self.api_token = os.getenv("GITHUB_TOKEN")
        
        if not self.api_token:
            logger.warning("GITHUB_TOKEN not found in environment")
            return
        
        try:
            self.client = github3.login(token=self.api_token)
            
            # Test connection
            user = self.client.me()
            logger.info(f"Connected to GitHub as: {user.login}")
            
            # Load initial data
            await self._load_repositories()
            
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            self.client = None
    
    async def _cleanup(self):
        """Cleanup resources."""
        # GitHub client doesn't need explicit cleanup
        pass
    
    async def _create_repository(self, repo: GitHubRepository) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.create_repository(
                name=repo.name,
                description=repo.description,
                private=repo.private,
                auto_init=repo.auto_init,
                gitignore_template=repo.gitignore_template,
                license_template=repo.license_template
            )
            
            result = {
                "id": repository.id,
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "private": repository.private,
                "html_url": repository.html_url,
                "clone_url": repository.clone_url,
                "ssh_url": repository.ssh_url
            }
            
            self.repositories_cache[repository.full_name] = result
            return result
        
        except Exception as e:
            logger.error(f"Error creating GitHub repository: {e}")
            raise
    
    async def _get_repositories(self) -> Dict[str, Any]:
        """Get all repositories."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repositories = []
            for repo in self.client.repositories():
                repo_data = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "html_url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "ssh_url": repo.ssh_url,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
                }
                repositories.append(repo_data)
                self.repositories_cache[repo.full_name] = repo_data
            
            return {"repositories": repositories}
        
        except Exception as e:
            logger.error(f"Error getting GitHub repositories: {e}")
            raise
    
    async def _create_issue(
        self,
        owner: str,
        repo: str,
        issue: GitHubIssue
    ) -> Dict[str, Any]:
        """Create a new GitHub issue."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            new_issue = repository.create_issue(
                title=issue.title,
                body=issue.body,
                labels=issue.labels or [],
                assignees=issue.assignees or []
            )
            
            result = {
                "id": new_issue.id,
                "number": new_issue.number,
                "title": new_issue.title,
                "body": new_issue.body,
                "state": new_issue.state,
                "html_url": new_issue.html_url,
                "labels": [label.name for label in new_issue.labels()],
                "assignees": [assignee.login for assignee in new_issue.assignees()]
            }
            
            # Cache the issue
            cache_key = f"{owner}/{repo}"
            if cache_key not in self.issues_cache:
                self.issues_cache[cache_key] = []
            self.issues_cache[cache_key].append(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            raise
    
    async def _get_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> Dict[str, Any]:
        """Get issues from a repository."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            issues = []
            
            for issue in repository.issues(state=state):
                issue_data = {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "html_url": issue.html_url,
                    "labels": [label.name for label in issue.labels()],
                    "assignees": [assignee.login for assignee in issue.assignees()],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None
                }
                issues.append(issue_data)
            
            return {"issues": issues}
        
        except Exception as e:
            logger.error(f"Error getting GitHub issues: {e}")
            raise
    
    async def _create_pr(
        self,
        owner: str,
        repo: str,
        pr: GitHubPR
    ) -> Dict[str, Any]:
        """Create a new GitHub pull request."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            new_pr = repository.create_pull(
                title=pr.title,
                body=pr.body,
                head=pr.head,
                base=pr.base
            )
            
            # Add labels and assignees if provided
            if pr.labels:
                new_pr.add_labels(*pr.labels)
            
            if pr.assignees:
                new_pr.add_assignees(*pr.assignees)
            
            result = {
                "id": new_pr.id,
                "number": new_pr.number,
                "title": new_pr.title,
                "body": new_pr.body,
                "state": new_pr.state,
                "head": new_pr.head.label,
                "base": new_pr.base.label,
                "html_url": new_pr.html_url,
                "labels": [label.name for label in new_pr.labels()],
                "assignees": [assignee.login for assignee in new_pr.assignees()]
            }
            
            # Cache the PR
            cache_key = f"{owner}/{repo}"
            if cache_key not in self.prs_cache:
                self.prs_cache[cache_key] = []
            self.prs_cache[cache_key].append(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating GitHub PR: {e}")
            raise
    
    async def _get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> Dict[str, Any]:
        """Get pull requests from a repository."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            pull_requests = []
            
            for pr in repository.pull_requests(state=state):
                pr_data = {
                    "id": pr.id,
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "head": pr.head.label,
                    "base": pr.base.label,
                    "html_url": pr.html_url,
                    "labels": [label.name for label in pr.labels()],
                    "assignees": [assignee.login for assignee in pr.assignees()],
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None
                }
                pull_requests.append(pr_data)
            
            return {"pull_requests": pull_requests}
        
        except Exception as e:
            logger.error(f"Error getting GitHub PRs: {e}")
            raise
    
    async def _create_branch(
        self,
        owner: str,
        repo: str,
        branch: GitHubBranch
    ) -> Dict[str, Any]:
        """Create a new branch."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            
            # Get the source branch (default to main)
            source_branch = branch.source_branch or "main"
            source_ref = repository.ref(f"heads/{source_branch}")
            
            if not source_ref:
                raise Exception(f"Source branch {source_branch} not found")
            
            # Create the new branch
            new_ref = repository.create_ref(
                f"refs/heads/{branch.name}",
                source_ref.object.sha
            )
            
            result = {
                "name": branch.name,
                "ref": new_ref.ref,
                "sha": new_ref.object.sha,
                "url": new_ref.url
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating GitHub branch: {e}")
            raise
    
    async def _get_branches(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get branches from a repository."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            branches = []
            
            for branch in repository.branches():
                branch_data = {
                    "name": branch.name,
                    "commit": {
                        "sha": branch.commit.sha,
                        "message": branch.commit.message,
                        "author": branch.commit.author.login if branch.commit.author else None
                    }
                }
                branches.append(branch_data)
            
            return {"branches": branches}
        
        except Exception as e:
            logger.error(f"Error getting GitHub branches: {e}")
            raise
    
    async def _create_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new file in a repository."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            repository = self.client.repository(owner, repo)
            
            # Create the file
            commit = repository.create_file(
                path=path,
                message=message,
                content=content,
                branch=branch
            )
            
            result = {
                "path": path,
                "sha": commit["content"]["sha"],
                "url": commit["content"]["url"],
                "html_url": commit["content"]["html_url"],
                "message": commit["commit"]["message"]
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating GitHub file: {e}")
            raise
    
    async def _get_workflows(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get GitHub Actions workflows."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            # Note: github3.py doesn't directly support workflows
            # This would require using the GitHub API directly
            # For now, return a placeholder
            return {
                "workflows": [],
                "message": "Workflow support requires direct GitHub API integration"
            }
        
        except Exception as e:
            logger.error(f"Error getting GitHub workflows: {e}")
            raise
    
    async def _trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main"
    ) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow."""
        if not self.client:
            raise Exception("GitHub client not initialized")
        
        try:
            # Note: github3.py doesn't directly support workflow triggers
            # This would require using the GitHub API directly
            # For now, return a placeholder
            return {
                "workflow_id": workflow_id,
                "ref": ref,
                "message": "Workflow trigger requires direct GitHub API integration"
            }
        
        except Exception as e:
            logger.error(f"Error triggering GitHub workflow: {e}")
            raise
    
    async def _load_repositories(self):
        """Load repositories into cache."""
        try:
            await self._get_repositories()
            logger.info(f"Loaded {len(self.repositories_cache)} repositories")
        except Exception as e:
            logger.error(f"Failed to load repositories: {e}")


# Create server instance
github_server = GitHubMCPServer()
app = github_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 