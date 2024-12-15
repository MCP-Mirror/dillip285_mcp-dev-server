"""Project representation and management."""
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
import git
from pydantic import BaseModel

class ProjectConfig(BaseModel):
    """Project configuration model."""
    
    name: str
    template: str
    description: str = ""
    version: str = "0.1.0"
    
class ProjectState:
    """Project state tracking."""
    
    def __init__(self):
        """Initialize project state."""
        self.git_initialized: bool = False
        self.last_build: Optional[Dict[str, Any]] = None
        self.last_test_run: Optional[Dict[str, Any]] = None
        self.active_environments: List[str] = []
        
class Project:
    """Project instance representation."""
    
    def __init__(self, path: str, config: ProjectConfig, state: ProjectState):
        """Initialize project instance.
        
        Args:
            path: Project directory path
            config: Project configuration
            state: Project state
        """
        self.id = str(uuid.uuid4())
        self.path = path
        self.config = config
        self.state = state
        
    def get_structure(self) -> Dict[str, Any]:
        """Get project directory structure.
        
        Returns:
            Dict[str, Any]: Directory structure
        """
        def scan_dir(path: Path) -> Dict[str, Any]:
            structure = {}
            
            for item in path.iterdir():
                if item.name.startswith("."):
                    continue
                    
                if item.is_file():
                    structure[item.name] = "file"
                elif item.is_dir():
                    structure[item.name] = scan_dir(item)
                    
            return structure
            
        return scan_dir(Path(self.path))
        
    def get_git_status(self) -> Dict[str, Any]:
        """Get Git repository status.
        
        Returns:
            Dict[str, Any]: Git status information
        """
        if not self.state.git_initialized:
            return {"initialized": False}
            
        try:
            repo = git.Repo(self.path)
            return {
                "initialized": True,
                "branch": repo.active_branch.name,
                "changed_files": [item.a_path for item in repo.index.diff(None)],
                "untracked_files": repo.untracked_files,
                "ahead": sum(1 for c in repo.iter_commits("origin/main..main")),
                "behind": sum(1 for c in repo.iter_commits("main..origin/main"))
            }
        except Exception as e:
            return {
                "initialized": False,
                "error": str(e)
            }
            
    async def create_git_commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a Git commit.
        
        Args:
            message: Commit message
            files: Optional list of files to commit
            
        Returns:
            Dict[str, Any]: Commit information
        """
        if not self.state.git_initialized:
            raise ValueError("Git is not initialized for this project")
            
        try:
            repo = git.Repo(self.path)
            
            if files:
                repo.index.add(files)
            else:
                repo.index.add("*")
                
            commit = repo.index.commit(message)
            
            return {
                "commit_id": commit.hexsha,
                "message": message,
                "author": str(commit.author),
                "files": [item.a_path for item in commit.stats.files]
            }
        except Exception as e:
            raise ValueError(f"Failed to create commit: {str(e)}")
            
    def get_dependencies(self) -> Dict[str, Any]:
        """Get project dependencies.
        
        Returns:
            Dict[str, Any]: Dependency information
        """
        dependencies = {}
        
        # Check Python dependencies
        req_file = Path(self.path) / "requirements.txt"
        if req_file.exists():
            with open(req_file, "r") as f:
                dependencies["python"] = f.read().splitlines()
                
        # Check Node.js dependencies
        package_file = Path(self.path) / "package.json"
        if package_file.exists():
            import json
            with open(package_file, "r") as f:
                package_data = json.load(f)
                dependencies["node"] = {
                    "dependencies": package_data.get("dependencies", {}),
                    "devDependencies": package_data.get("devDependencies", {})
                }
                
        return dependencies
        
    def analyze_code(self) -> Dict[str, Any]:
        """Analyze project code.
        
        Returns:
            Dict[str, Any]: Code analysis results
        """
        analysis = {
            "files": {},
            "summary": {
                "total_files": 0,
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "blank_lines": 0
            }
        }
        
        def analyze_file(path: Path) -> Dict[str, Any]:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
            code_lines = total_lines - blank_lines - comment_lines
            
            return {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines
            }
            
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        file_analysis = analyze_file(file_path)
                        relative_path = str(file_path.relative_to(self.path))
                        analysis["files"][relative_path] = file_analysis
                        
                        # Update summary
                        for key in ["total_lines", "code_lines", "comment_lines", "blank_lines"]:
                            analysis["summary"][key] += file_analysis[key]
                            
                        analysis["summary"]["total_files"] += 1
                    except Exception:
                        continue
                        
        return analysis
        
    def get_test_coverage(self) -> Dict[str, Any]:
        """Get test coverage information.
        
        Returns:
            Dict[str, Any]: Test coverage data
        """
        try:
            import coverage
            
            cov = coverage.Coverage()
            cov.load()
            
            return {
                "total_coverage": cov.report(),
                "missing_lines": dict(cov.analysis2()),
                "branch_coverage": cov.get_option("branch"),
                "excluded_lines": cov.get_exclude_list()
            }
        except Exception:
            return {
                "error": "Coverage data not available"
            }
            
    def get_ci_config(self) -> Dict[str, Any]:
        """Get CI configuration.
        
        Returns:
            Dict[str, Any]: CI configuration data
        """
        ci_configs = {}
        
        # Check GitHub Actions
        github_dir = Path(self.path) / ".github" / "workflows"
        if github_dir.exists():
            ci_configs["github_actions"] = []
            for workflow in github_dir.glob("*.yml"):
                with open(workflow, "r") as f:
                    ci_configs["github_actions"].append({
                        "name": workflow.stem,
                        "config": f.read()
                    })
                    
        # Check GitLab CI
        gitlab_file = Path(self.path) / ".gitlab-ci.yml"
        if gitlab_file.exists():
            with open(gitlab_file, "r") as f:
                ci_configs["gitlab"] = f.read()
                
        return ci_configs
        
    async def cleanup(self):
        """Clean up project resources."""
        # Implementation will depend on what resources need cleanup
        pass