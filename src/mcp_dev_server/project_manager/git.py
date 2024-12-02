"""Git integration for MCP Development Server."""
import os
from typing import List, Optional
from git import Repo, GitCommandError
from git.objects import Commit

from ..utils.logging import setup_logging
from ..utils.errors import GitError

logger = setup_logging(__name__)

class GitManager:
    """Manages Git operations for a project."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.repo: Optional[Repo] = None
        
    async def initialize(self) -> None:
        """Initialize Git repository."""
        try:
            self.repo = Repo.init(self.project_path)
            
            # Create default .gitignore if it doesn't exist
            gitignore_path = os.path.join(self.project_path, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write('\n'.join([
                        '# Python',
                        '__pycache__/',
                        '*.pyc',
                        '*.pyo',
                        '*.pyd',
                        '.Python',
                        'env/',
                        'venv/',
                        '.env',
                        '.venv',
                        '',
                        '# IDE',
                        '.idea/',
                        '.vscode/',
                        '*.swp',
                        '*.swo',
                        '',
                        '# Project specific',
                        '.mcp/',
                        'dist/',
                        'build/',
                        '*.egg-info/',
                        ''
                    ]))
                
            # Initial commit
            if not self.repo.heads:
                self.repo.index.add(['.gitignore'])
                self.repo.index.commit("Initial commit")
                
            logger.info(f"Initialized Git repository at {self.project_path}")
            
        except Exception as e:
            raise GitError(f"Git initialization failed: {str(e)}")
            
    async def get_status(self) -> dict:
        """Get repository status."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            return {
                "branch": self.repo.active_branch.name,
                "changed_files": [item.a_path for item in self.repo.index.diff(None)],
                "untracked_files": self.repo.untracked_files,
                "is_dirty": self.repo.is_dirty(),
                "head_commit": {
                    "hash": self.repo.head.commit.hexsha,
                    "message": self.repo.head.commit.message,
                    "author": str(self.repo.head.commit.author),
                    "date": str(self.repo.head.commit.authored_datetime)
                }
            }
            
        except Exception as e:
            raise GitError(f"Failed to get Git status: {str(e)}")
            
    async def commit(self, message: str, files: Optional[List[str]] = None) -> str:
        """Create a new commit."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            # Add specified files or all changes
            if files:
                self.repo.index.add(files)
            else:
                self.repo.index.add('.')
                
            # Create commit
            commit = self.repo.index.commit(message)
            logger.info(f"Created commit: {commit.hexsha}")
            
            return commit.hexsha
            
        except Exception as e:
            raise GitError(f"Failed to create commit: {str(e)}")
            
    async def get_commit_history(
        self,
        max_count: Optional[int] = None
    ) -> List[dict]:
        """Get commit history."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            commits = []
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    "hash": commit.hexsha,
                    "message": commit.message,
                    "author": str(commit.author),
                    "date": str(commit.authored_datetime),
                    "files": list(commit.stats.files.keys())
                })
                
            return commits
            
        except Exception as e:
            raise GitError(f"Failed to get commit history: {str(e)}")
            
    async def create_branch(self, name: str) -> None:
        """Create a new branch."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            self.repo.create_head(name)
            logger.info(f"Created branch: {name}")
            
        except Exception as e:
            raise GitError(f"Failed to create branch: {str(e)}")
            
    async def checkout(self, branch: str) -> None:
        """Checkout a branch."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            self.repo.git.checkout(branch)
            logger.info(f"Checked out branch: {branch}")
            
        except Exception as e:
            raise GitError(f"Failed to checkout branch: {str(e)}")
            
    async def get_diff(
        self,
        commit_a: Optional[str] = None,
        commit_b: Optional[str] = None
    ) -> str:
        """Get diff between commits or working directory."""
        try:
            if not self.repo:
                raise GitError("Git repository not initialized")
                
            return self.repo.git.diff(commit_a, commit_b)
            
        except Exception as e:
            raise GitError(f"Failed to get diff: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up Git resources."""
        self.repo = None