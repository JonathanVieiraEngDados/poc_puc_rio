from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_csv_agent
from langchain.agents import AgentType

from app.dataPrep.dataset_repository import DatasetRepository
from app.tools import (
    ParseRouteTool,
    MainRateTool,
    TopOffendersTool,
    GetAvailableDatesTool,
    MathOperatorTools,
)
from langchain_core.tools import StructuredTool


class LogisticsAgent:
    """
    Agente logístico (versão POC)
    - Igual ao design original (sem LangGraph)
    - Compatível com tools baseadas em __call__
    """

    def __init__(
        self,
        csv_path: str,
        rules: str,
        model: str = "gpt-5",
        temperature: float = 0.0,
        verbose: bool = True,
    ):
        # 1️ Carregar e tratar o dataset
        self.repo = DatasetRepository(csv_path)
        self.repo.load()

        # 2️ Tools: wrap bound methods as StructuredTool to avoid 'self' collisions
        parse_route = ParseRouteTool().run
        main_rate = MainRateTool(self.repo).run
        top_offenders = TopOffendersTool(self.repo).run
        get_available_dates = GetAvailableDatesTool(self.repo).run

        self.tools = [
            StructuredTool.from_function(parse_route, name="parseRoute"),
            StructuredTool.from_function(main_rate, name="mainRate"),
            StructuredTool.from_function(top_offenders, name="topOffenders"),
            StructuredTool.from_function(get_available_dates, name="getAvailableDates"),
        ]

        # Add math operator tools (flattened, not nested)
        self.tools += MathOperatorTools.as_tools()

        # 3️ Modelo
        llm = ChatOpenAI(model=model, temperature=temperature)

        # 4️ Criação do agente (igual ao código original)
        self.agent = create_csv_agent(
           llm,
           path=csv_path,
           verbose=verbose,
           agent_type=AgentType.OPENAI_FUNCTIONS,
           allow_dangerous_code=True,
           prefix=rules,
           extra_tools=self.tools, 
        )

    def ask(self, prompt: str) -> str:
        """Executa a consulta natural e retorna a resposta do agente."""
        try:
            result = self.agent.invoke({"input": prompt})
            if isinstance(result, dict) and "output" in result:
                return result["output"]
            return str(result)
        except Exception as e:
            return f"[Erro na execução do agente] {e}"

    def batch(self, prompts: list[str]) -> list[str]:
        """Executa uma lista de perguntas em sequência."""
        return [self.ask(p) for p in prompts]