"""Development workflow management for MCP Development Server."""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio

from ..utils.errors import WorkflowError
from ..utils.logging import setup_logging

logger = setup_logging(__name__)

class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowStep:
    """Individual step in a workflow."""
    
    def __init__(
        self,
        name: str,
        command: str,
        environment: str,
        depends_on: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        retry_count: int = 0
    ):
        self.name = name
        self.command = command
        self.environment = environment
        self.depends_on = depends_on or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.status = WorkflowStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.attempts = 0

class WorkflowManager:
    """Manages development workflows."""
    
    def __init__(self, env_manager):
        self.env_manager = env_manager
        self.workflows: Dict[str, Dict[str, Any]] = {}
        
    async def create_workflow(
        self,
        steps: List[WorkflowStep],
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new workflow."""
        try:
            workflow_id = f"workflow_{len(self.workflows)}"
            
            # Initialize workflow
            self.workflows[workflow_id] = {
                "steps": steps,
                "config": config or {},
                "status": WorkflowStatus.PENDING,
                "start_time": None,
                "end_time": None
            }
            
            return workflow_id
            
        except Exception as e:
            raise WorkflowError(f"Failed to create workflow: {str(e)}")
            
    async def start_workflow(self, workflow_id: str) -> None:
        """Start workflow execution."""
        try:
            if workflow := self.workflows.get(workflow_id):
                workflow["status"] = WorkflowStatus.RUNNING
                workflow["start_time"] = datetime.now()
                
                # Execute workflow steps
                asyncio.create_task(self._execute_workflow(workflow_id))
                
            else:
                raise WorkflowError(f"Workflow not found: {workflow_id}")
                
        except Exception as e:
            raise WorkflowError(f"Failed to start workflow: {str(e)}")
            
    async def _execute_workflow(self, workflow_id: str) -> None:
        """Execute workflow steps in order."""
        workflow = self.workflows[workflow_id]
        
        try:
            # Build execution graph
            graph = self._build_execution_graph(workflow["steps"])
            
            # Execute steps in dependency order
            for step_group in graph:
                results = await asyncio.gather(
                    *[self._execute_step(workflow_id, step) for step in step_group],
                    return_exceptions=True
                )
                
                # Check for failures
                if any(isinstance(r, Exception) for r in results):
                    workflow["status"] = WorkflowStatus.FAILED
                    return
                    
            workflow["status"] = WorkflowStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            workflow["status"] = WorkflowStatus.FAILED
            workflow["error"] = str(e)
            
        finally:
            workflow["end_time"] = datetime.now()
            
    async def _execute_step(
        self,
        workflow_id: str,
        step: WorkflowStep
    ) -> None:
        """Execute a single workflow step."""
        try:
            step.status = WorkflowStatus.RUNNING
            step.attempts += 1
            
            # Execute step command
            result = await asyncio.wait_for(
                self.env_manager.execute_in_environment(
                    step.environment,
                    step.command
                ),
                timeout=step.timeout
                )
            
            # Handle step result
            success = result["exit_code"] == 0
            step.result = {
                "output": result["output"],
                "error": result.get("error"),
                "exit_code": result["exit_code"]
            }
            
            if success:
                step.status = WorkflowStatus.COMPLETED
            else:
                # Handle retry logic
                if step.attempts < step.retry_count + 1:
                    logger.info(f"Retrying step {step.name} (attempt {step.attempts})")
                    return await self._execute_step(workflow_id, step)
                step.status = WorkflowStatus.FAILED
                
        except asyncio.TimeoutError:
            step.status = WorkflowStatus.FAILED
            step.result = {
                "error": "Step execution timed out"
            }
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.result = {
                "error": str(e)
            }
            
    def _build_execution_graph(
        self,
        steps: List[WorkflowStep]
    ) -> List[List[WorkflowStep]]:
        """Build ordered list of step groups based on dependencies."""
        # Initialize variables
        graph: List[List[WorkflowStep]] = []
        completed = set()
        remaining = set(step.name for step in steps)
        steps_by_name = {step.name: step for step in steps}
        
        while remaining:
            # Find steps with satisfied dependencies
            group = set()
            for step_name in remaining:
                step = steps_by_name[step_name]
                if all(dep in completed for dep in step.depends_on):
                    group.add(step_name)
            
            if not group:
                # Circular dependency detected
                raise WorkflowError("Circular dependency detected in workflow steps")
            
            # Add group to graph
            graph.append([steps_by_name[name] for name in group])
            completed.update(group)
            remaining.difference_update(group)
            
        return graph
        
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status and results of a workflow."""
        if workflow := self.workflows.get(workflow_id):
            return {
                "id": workflow_id,
                "status": workflow["status"],
                "steps": [
                    {
                        "name": step.name,
                        "status": step.status,
                        "result": step.result,
                        "attempts": step.attempts
                    }
                    for step in workflow["steps"]
                ],
                "start_time": workflow["start_time"],
                "end_time": workflow["end_time"],
                "error": workflow.get("error")
            }
        raise WorkflowError(f"Workflow not found: {workflow_id}")

    def get_common_workflows(self) -> Dict[str, List[WorkflowStep]]:
        """Get predefined common workflow templates."""
        return {
            "build": [
                WorkflowStep(
                    name="install",
                    command="npm install",
                    environment="default"
                ),
                WorkflowStep(
                    name="lint",
                    command="npm run lint",
                    environment="default",
                    depends_on=["install"]
                ),
                WorkflowStep(
                    name="test",
                    command="npm test",
                    environment="default", 
                    depends_on=["install"]
                ),
                WorkflowStep(
                    name="build",
                    command="npm run build",
                    environment="default",
                    depends_on=["lint", "test"]
                )
            ],
            "test": [
                WorkflowStep(
                    name="install_deps",
                    command="npm install",
                    environment="default"
                ),
                WorkflowStep(
                    name="unit_tests",
                    command="npm run test:unit",
                    environment="default",
                    depends_on=["install_deps"]
                ),
                WorkflowStep(
                    name="integration_tests", 
                    command="npm run test:integration",
                    environment="default",
                    depends_on=["install_deps"]
                ),
                WorkflowStep(
                    name="coverage",
                    command="npm run coverage",
                    environment="default",
                    depends_on=["unit_tests", "integration_tests"]
                )
            ],
            "release": [
                WorkflowStep(
                    name="bump_version",
                    command="npm version patch",
                    environment="default"
                ),
                WorkflowStep(
                    name="build",
                    command="npm run build",
                    environment="default",
                    depends_on=["bump_version"]
                ),
                WorkflowStep(
                    name="publish",
                    command="npm publish",
                    environment="default",
                    depends_on=["build"]
                )
            ]
        }