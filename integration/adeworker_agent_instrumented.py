"""
Instrumented ADEWorker DevAgent Example

This file shows how to instrument the actual ADEWorker BaseDevAgent
with AgentEval trace collection.

IMPORTANT: This is an example. To integrate with your actual ADEWorker:
1. Copy the decorators from adeworker_plugin.py
2. Add decorators to your agent methods as shown below
3. Initialize the plugin in your application startup
"""

import time
import json
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

# Import from ADEWorker (adjust paths as needed)
# from worker.infra.logging import logger_factory
# from worker.repository.repo_manager import FileWriter, FileReader
# from worker.repository.models import ChangePlan, FileItem, RepoMetadata
# from worker.runtime_env.models import DockerEnvMetadata
# from worker.runtime_env.docker_runtime_env import DockerRuntimeEnv
# from ..agent_base.model import UserInput, UserFeedback, TechDocument, LogAnalysis
# from ..agent_base.base_agent import BaseAgent
# from ..micro_agents.repo_analysis_ma import RepoAnalysisAgent, RepoAnalysisPromptValue
# from ..micro_agents.requirement_analysis_ma import RequirementAnalysisAgent, RequirementAnalysisPromptValue
# from ..micro_agents.tech_design_ma import TechDesignAgent, TechDesignPromptValue
# from ..micro_agents.coder_ma import CoderMicroAgent, CoderPromptValue
# from ..micro_agents.log_analysis_ma import LogAnalysisAgent, LogAnalysisPromptValue
# from .state import DevState, LogStage

# Import AgentEval plugin decorators
from adeworker_plugin import instrument_agent, instrument_node


# LOGGER = logger_factory.get_logger()
# checkpointer = InMemorySaver()


class InstrumentedDevAgent:
    """
    Example of instrumented DevAgent

    Key changes from original:
    1. Added @instrument_agent decorator to arun() and astream_run()
    2. Added @instrument_node decorators to all node methods
    3. No other code changes needed!
    """

    def __init__(self, llm, rules: str):
        self.llm = llm
        self.rules = rules
        self.workflow = self._build_workflow()

        # Sub Agents
        # self.repo_analysis_agent = RepoAnalysisAgent(llm, rules)
        # self.requirement_analysis_agent = RequirementAnalysisAgent(llm, rules)
        # self.tech_design_agent = TechDesignAgent(llm, rules)
        # self.coder_agent = CoderMicroAgent(llm, rules)
        # self.log_analysis_agent = LogAnalysisAgent(llm, rules)

        # super().__init__(llm, rules)

    # ===== Instrumented Agent Methods =====

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        """
        Instrumented arun method - now collects traces!

        Changes:
        - Added @instrument_agent decorator
        - No other changes to the method body
        """
        # state = DevState(input=user_input)

        # state = await self.workflow.ainvoke(
        #     input=state,
        #     config={"configurable": {"thread_id": user_input.task_id}}
        # )

        # return state
        pass

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def astream_run(self, user_input):
        """
        Instrumented astream_run method - now collects traces!

        Changes:
        - Added @instrument_agent decorator
        - No other changes to the method body
        """
        # state = DevState(input=user_input)

        # async for step_state in self.workflow.astream(
        #     input=state,
        #     config={"configurable": {"thread_id": user_input.task_id}},
        #     stream_mode="values"
        # ):
        #     yield step_state
        pass

    # ===== Instrumented Node Methods =====

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state):
        """
        Instrumented prepare_context node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Received request and prepare context with state: %s", state)

        # state.repo_metadata = RepoMetadata(repo_dir=state.input.repo_ws_path)
        # state.output.message = f"接收到任务，开始处理"
        # state.output.status = "started"

        # return state
        pass

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state):
        """
        Instrumented understand_repo node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Start to understand the repo code...")

        # repo_codes = FileReader().apply(state.repo_metadata.repo_dir)
        # result = self.repo_analysis_agent.run(RepoAnalysisPromptValue(codes=json.dumps(repo_codes)))

        # file_path = f".ade/task/{state.input.task_id}/repo_summary.md"
        # change_plan = ChangePlan(files=[FileItem(path=file_path, content=result)])
        # FileWriter(root=state.repo_metadata.repo_dir).apply(change_plan)

        # state.repo_analysis = TechDocument(doc_content=result, doc_path=file_path)
        # state.output.message = f"完成现有代码的理解，文件路径为：{file_path}"
        # state.output.status = "requirement_analysis"

        # LOGGER.info("Complete understanding the repo code!")

        # return state
        pass

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state):
        """
        Instrumented gen_requirement node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Start to understand user's idea and optimize the requirement...")

        # result = self.requirement_analysis_agent.run(RequirementAnalysisPromptValue(
        #     task_desc=state.input.task_desc,
        #     code_instruction=state.repo_analysis.doc_content
        # ))

        # file_path = f".ade/task/{state.input.task_id}/requirement.md"
        # change_plan = ChangePlan(files=[FileItem(path=file_path, content=result)])
        # FileWriter(root=state.repo_metadata.repo_dir).apply(change_plan)

        # state.requirement_doc = TechDocument(doc_content=result, doc_path=file_path)
        # state.output.message = f"完成需求分析，文件路径为：{file_path}"
        # state.output.status = "requirement_confirmation"

        # LOGGER.info("Complete optimizing the requirement!")

        # return state
        pass

    @instrument_node(node_name="gen_solution")
    def _node_gen_solution(self, state):
        """
        Instrumented gen_solution node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Start to design the solution...")

        # result = self.tech_design_agent.run(TechDesignPromptValue(
        #     requirement=state.requirement_doc.doc_content,
        #     code_instruction=state.repo_analysis.doc_content
        # ))

        # file_path = f".ade/task/{state.input.task_id}/design.md"
        # change_plan = ChangePlan(files=[FileItem(path=file_path, content=result)])
        # FileWriter(root=state.repo_metadata.repo_dir).apply(change_plan)

        # state.solution_doc = TechDocument(doc_content=result, doc_path=file_path)
        # state.output.message = f"完成方案设计，文件路径为：{file_path}"
        # state.output.status = "design_review"

        # LOGGER.info("Complete designing the solution!")

        # return state
        pass

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state):
        """
        Instrumented gen_code node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Start to generating the code...")

        # code_plan = self.coder_agent.run(CoderPromptValue(
        #     repo_dir=state.repo_metadata.repo_dir,
        #     solution=state.solution_doc.doc_content,
        #     codes=state.code_change.model_dump_json(),
        #     test_operation=state.tests_log_state.opertion,
        #     test_log=state.tests_log_state.log_content,
        #     test_failure_reason=state.tests_log_state.log_analysis.failure_reason,
        #     fix_solution=state.tests_log_state.log_analysis.solution
        # ))

        # changed_codes = FileWriter(root=state.repo_metadata.repo_dir).apply(code_plan)

        # state.code_change = code_plan
        # state.output.message = f"完成代码编写，代码路径为：{changed_codes}"
        # state.output.status = "coding"
        # state.code_iteration_times += 1

        # time.sleep(5)

        # LOGGER.info("Complete generating the code!")

        # return state
        pass

    @instrument_node(node_name="run_tests")
    def _node_run_tests(self, state):
        """
        Instrumented run_tests node

        Changes:
        - Added @instrument_node decorator
        - No other changes to the method body
        """
        # LOGGER.info("Start the generated APP for testing")
        # state.output.status = "testing"
        # state.output.message = f"代码测试中..."

        # code_change = state.code_change.model_dump_json()

        # docker_env_medatata = DockerEnvMetadata()
        # docker_env_medatata.env_name = state.repo_metadata.repo_name.lower()
        # docker_env_medatata.compose_file_dir = state.repo_metadata.repo_dir
        # docker_env_medatata.compose_file_name = "docker-compose.yml"
        # docker_env_medatata.master_container.service_name = "ctl_device"
        # docker_env_medatata.master_container.ssh_username = "root"
        # docker_env_medatata.master_container.ssh_password = "root"
        # test_cmd = ["robot", "tests"]

        # runtime_env = DockerRuntimeEnv(docker_env_medatata)

        # cmd, log, _ = runtime_env.start_env()
        # state.tests_log_state = self._analyze_log(code_change, f"启动环境，执行命令为：{cmd}", log)
        # if not state.tests_log_state.log_analysis.is_execution_success:
        #     return state

        # cmd, log, _ = runtime_env.exec_cmd(test_cmd)
        # state.tests_log_state = self._analyze_log(code_change, f"执行测试，执行命令为：{cmd}", log)

        # runtime_env.stop_env()

        # return state
        pass

    @instrument_node(node_name="wait_requirement_confirmation")
    def _node_wait_requirement_confirmation(self, state):
        """Instrumented wait_requirement_confirmation node"""
        # LOGGER.info("Waiting for user's requirement confirmation")
        # user_feedback_dict = interrupt("请评审需求文档！")
        # state.requirement_review = UserFeedback.model_validate(user_feedback_dict)
        # return state
        pass

    @instrument_node(node_name="wait_solution_review")
    def _node_wait_solution_review(self, state):
        """Instrumented wait_solution_review node"""
        # LOGGER.info("Waiting for user's solution review")
        # user_feedback_dict = interrupt("请评审方案文档！")
        # state.solution_review = UserFeedback.model_validate(user_feedback_dict)
        # return state
        pass

    @instrument_node(node_name="wait_code_review")
    def _node_wait_code_review(self, state):
        """Instrumented wait_code_review node"""
        # LOGGER.info("Waiting for user's code review")
        # user_feedback_dict = interrupt("请评审代码变更！")
        # state.code_review = UserFeedback.model_validate(user_feedback_dict)
        # return state
        pass

    @instrument_node(node_name="close")
    def _node_close(self, state):
        """Instrumented close node"""
        # LOGGER.info("Building final output with state: %s", state)
        # return state
        pass

    def _build_workflow(self):
        """Build workflow - no changes needed"""
        # Original workflow building code
        pass


# Summary of changes:
# 1. Import instrument_agent and instrument_node from adeworker_plugin
# 2. Add @instrument_agent to arun() and astream_run()
# 3. Add @instrument_node to all node methods
# 4. That's it! No other code changes needed
