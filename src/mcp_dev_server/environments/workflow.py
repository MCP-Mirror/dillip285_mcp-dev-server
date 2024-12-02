"""Development workflow management for environments."""
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio

from ..utils.logging import setup_logging
from ..utils.errors import WorkflowError

logger = setup_logging(__name__)

class TaskStatus(str, Enum):
    """Workflow task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Task:
    """Represents a workflow task."""
    
    def __init__(
        self,
        name: str,
        command: str,
        environment: str,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None
    ):
        self.name = name
        self.command = command
        self.environment = environment
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.on_success = on_success
        self.on_failure = on_failure
        self.attempts = 0

class Workflow:
    """Manages development workflows."""
    
    def __init__(self, env_manager):
        self.env_manager = env_manager
        self.tasks: Dict[str, Task] = {}
        self.running = False
        
    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self.tasks[task.name] = task
        
    def remove_task(self, task_name: str) -> None:
        """Remove a task from the workflow."""
        if task_name in self.tasks:
            del self.tasks[task_name]
            
    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow."""
        try:
            self.running = True
            results = {}
            
            # Build dependency graph
            graph = self._build_dependency_graph()
            
            # Execute tasks in order
            for task_group in graph:
                # Execute tasks in group concurrently
                tasks = [self._execute_task(task_name) for task_name in task_group]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for task_name, result in zip(task_group, group_results):
                    if isinstance(result, Exception):
                        self.tasks[task_name].status = TaskStatus.FAILED
                        results[task_name] = {
                            "status": TaskStatus.FAILED,
                            "error": str(result)
                        }
                    else:
                        results[task_name] = result
                
            return results
            
        except Exception as e:
            raise WorkflowError(f"Workflow execution failed: {str(e)}")
        finally:
            self.running = False
            
    async def _execute_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a single task."""
        task = self.tasks[task_name]
        
        # Check dependencies
        for dep in task.dependencies:
            dep_task = self.tasks.get(dep)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.SKIPPED
                return {
                    "status": TaskStatus.SKIPPED,
                    "reason": f"Dependency {dep} not satisfied"
                }
        
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        
        try:
            # Execute the command
            result = await asyncio.wait_for(
                self.env_manager.execute_in_environment(
                    task.environment,
                    task.command
                ),
                timeout=task.timeout
            )
            
            # Handle execution result
            if result['exit_code'] == 0:
                task.status = TaskStatus.COMPLETED
                if task.on_success:
                    await task.on_success(result)
                return {
                    "status": TaskStatus.COMPLETED,
                    "result": result
                }
            else:
                # Handle retry logic
                if task.attempts < task.retry_count + 1:
                    logger.info(f"Retrying task {task_name} (attempt {task.attempts})")
                    return await self._execute_task(task_name)
                
                task.status = TaskStatus.FAILED
                if task.on_failure:
                    await task.on_failure(result)
                return {
                    "status": TaskStatus.FAILED,
                    "result": result
                }
                
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            return {
                "status": TaskStatus.FAILED,
                "error": "Task timeout"
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            return {
                "status": TaskStatus.FAILED,
                "error": str(e)
            }
            
    def _build_dependency_graph(self) -> List[List[str]]:
        """Build ordered list of task groups based on dependencies."""
        # Initialize variables
        graph: List[List[str]] = []
        completed = set()
        remaining = set(self.tasks.keys())
        
        while remaining:
            # Find tasks with satisfied dependencies
            group = set()
            for task_name in remaining:
                task = self.tasks[task_name]
                if all(dep in completed for dep in task.dependencies):
                    group.add(task_name)
            
            if not group:
                # Circular dependency detected
                raise WorkflowError("Circular dependency detected in workflow")
            
            # Add group to graph
            graph.append(list(group))
            completed.update(group)
            remaining.difference_update(group)
            
        return graph
        
    def get_status(self) -> Dict[str, Any]:
        """Get workflow status."""
        return {
            "running": self.running,
            "tasks": {
                name: {
                    "status": task.status,
                    "attempts": task.attempts,
                    "dependencies": task.dependencies
                }
                for name, task in self.tasks.items()
            }
        }
        
    def reset(self) -> None:
        """Reset workflow state."""
        for task in self.tasks.values():
            task.status = TaskStatus.PENDING
            task.attempts = 0
            task.result = None
        self.running = False

# Example workflow definitions for common development tasks
class CommonWorkflows:
    """Predefined development workflows."""
    
    @staticmethod
    def create_build_workflow(env_manager, environment: str) -> Workflow:
        """Create a standard build workflow."""
        workflow = Workflow(env_manager)
        
        # Install dependencies
        workflow.add_task(Task(
            name="install_deps",
            command="npm install",
            environment=environment,
            retry_count=2
        ))
        
        # Run linter
        workflow.add_task(Task(
            name="lint",
            command="npm run lint",
            environment=environment,
            dependencies=["install_deps"]
        ))
        
        # Run tests
        workflow.add_task(Task(
            name="test",
            command="npm run test",
            environment=environment,
            dependencies=["install_deps"]
        ))
        
        # Build
        workflow.add_task(Task(
            name="build",
            command="npm run build",
            environment=environment,
            dependencies=["lint", "test"]
        ))
        
        return workflow
        
    @staticmethod
    def create_test_workflow(env_manager, environment: str) -> Workflow:
        """Create a standard test workflow."""
        workflow = Workflow(env_manager)
        
        # Install test dependencies
        workflow.add_task(Task(
            name="install_test_deps",
            command="npm install --only=dev",
            environment=environment,
            retry_count=2
        ))
        
        # Run unit tests
        workflow.add_task(Task(
            name="unit_tests",
            command="npm run test:unit",
            environment=environment,
            dependencies=["install_test_deps"]
        ))
        
        # Run integration tests
        workflow.add_task(Task(
            name="integration_tests",
            command="npm run test:integration",
            environment=environment,
            dependencies=["install_test_deps"]
        ))
        
        # Generate coverage report
        workflow.add_task(Task(
            name="coverage",
            command="npm run coverage",
            environment=environment,
            dependencies=["unit_tests", "integration_tests"]
        ))
        
        return workflow