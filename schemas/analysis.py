from typing import List, Optional, Union, List, Tuple
from pydantic import BaseModel, Field

# --- Chart Data Models ---

class BaseChart(BaseModel):
    """Base model to include common fields if any, e.g., title."""
    section: str # Reference back to the section number (e.g., "1.1", "1.2")

class BarGroupedChart(BaseChart):
    chart_type: str = Field("bar_grouped", Literal=True)
    labels: List[str] = Field(..., description="Labels for the bars/groups.")
    # Allow flexibility: sometimes one dataset, sometimes two (e.g., budgeted vs paid)
    values_1: List[Optional[float]] = Field(..., description="First set of values for the bars.")
    values_2: Optional[List[Optional[float]]] = Field(None, description="Second set of values for grouped bars (optional).")
    legend: Optional[List[str]] = Field(None, description="Legend labels if multiple value sets are used (e.g., ['Orçado', 'Pago']).")

class PieChart(BaseChart):
    chart_type: str = Field("pie", Literal=True)
    labels: List[str] = Field(..., description="Labels for the pie slices.")
    values: List[Optional[float]] = Field(..., description="Values for the pie slices.")

class BarStackedChart(BaseChart):
    chart_type: str = Field("bar_stacked", Literal=True)
    labels: List[str] = Field(..., description="Labels for the bars.")
    values_1: List[Optional[float]] = Field(..., description="Values for the first stack layer.")
    values_2: List[Optional[float]] = Field(..., description="Values for the second stack layer.")
    legend: List[str] = Field(..., description="Legend labels for the stack layers (e.g., ['Orçado', 'Pago']).")

class HeatmapChart(BaseChart):
    chart_type: str = Field("heatmap", Literal=True)
    rows: List[str] = Field(..., description="Row labels for the heatmap.")
    columns: List[str] = Field(..., description="Column labels for the heatmap.")
    # List of lists representing the heatmap values, matching rows and columns
    values: List[List[Optional[float]]] = Field(..., description="Heatmap cell values (list of lists).")

class LineChart(BaseChart):
    chart_type: str = Field("line", Literal=True)
    # Assuming x-axis can be numbers (years) or strings
    x: List[Union[int, str]] = Field(..., description="X-axis values (e.g., years).")
    y: List[Optional[float]] = Field(..., description="Y-axis values.")
    label: str = Field(..., description="Label for the line.")

# Union type for any possible chart associated with a section
AnyChart = Union[BarGroupedChart, PieChart, BarStackedChart, HeatmapChart, LineChart]

# --- Report Section Models ---

class ReportSection(BaseModel):
    """Represents a main section of the analysis text."""
    text: str = Field(..., description="The textual analysis for this section.")
    # A section might have zero or one chart
    chart_data: Optional[AnyChart] = Field(None, description="Data required to render the chart for this section, if applicable.")


class FinancialAnalysisSubsections(BaseModel):
    receitas_despesas: ReportSection = Field(..., alias="1.1", description="Analysis of Revenue vs Expenses.")
    principais_fontes_receita: ReportSection = Field(..., alias="1.2", description="Analysis of Main Revenue Sources.")
    areas_maior_execucao: ReportSection = Field(..., alias="1.3", description="Analysis of High-Execution Areas (>= 70%).")
    areas_baixa_execucao: ReportSection = Field(..., alias="1.4", description="Analysis of Low-Execution Areas (<= 30%).")

class ProjectionsRecommendationsSubsections(BaseModel):
    projecoes: ReportSection = Field(..., alias="3.1", description="Projections Discussion.")
    recomendacoes: ReportSection = Field(..., alias="3.2", description="Recommendations List (Text Only).")

# --- Top-Level Response Model ---

class AnalysisResponse(BaseModel):
    """Structured financial analysis report including text and chart data."""
    municipio_nome: str = Field(..., description="Name of the municipality.")
    exercicio_ano: Union[int, str] = Field(..., description="The fiscal year of the analysis.")
    fonte_pdf_nome: str = Field(..., description="Filename of the source PDF/CSV provided.")
    
    analise_financeira: FinancialAnalysisSubsections = Field(..., description="Section 1: Financial Analysis")
    avaliacao_riscos: ReportSection = Field(..., description="Section 2: Risk Assessment")
    projecoes_recomendacoes: ProjectionsRecommendationsSubsections = Field(..., description="Section 3: Projections and Recommendations")
    conclusao: ReportSection = Field(..., description="Section 4: Conclusion")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "municipio_nome": "Exemploville",
                    "exercicio_ano": 2023,
                    "fonte_pdf_nome": "orcamento_2023.csv",
                    "analise_financeira": {
                        "1.1": {
                            "text": "A receita total orçada foi de R$ 10.000.000,00. As despesas empenhadas somaram R$ 9.500.000,00 (95,0% do orçado), as liquidadas R$ 9.000.000,00 (90,0%) e as pagas R$ 8.800.000,00 (88,0%).",
                            "chart_data": {
                                "chart_type": "bar_grouped",
                                "section": "1.1",
                                "labels": ["Receita orçada", "Despesas empenhadas", "Despesas liquidadas", "Despesas pagas"],
                                "values_1": [10000000.00, 9500000.00, 9000000.00, 8800000.00]
                            }
                        },
                        "1.2": {
                             "text": "As principais fontes foram IPTU (R$ 3M pagos / 98% exec), ISS (R$ 2.5M / 95%), FPM (R$ 2M / 100%) e ICMS (R$ 1.5M / 90%).",
                             "chart_data": {
                                 "chart_type": "pie",
                                 "section": "1.2",
                                 "labels": ["IPTU", "ISS", "FPM", "ICMS"],
                                 "values": [3000000.0, 2500000.0, 2000000.0, 1500000.0]
                             }
                        },
                         "1.3": { "text": "Educação (95%), Saúde (92%), Urbanismo (88%) tiveram alta execução.", "chart_data": None },
                         "1.4": { "text": "Cultura (25%), Esporte (20%), Meio Ambiente (15%) tiveram baixa execução.", "chart_data": None }
                    },
                    "avaliacao_riscos": {
                        "text": "Riscos Financeiros: ... Riscos Operacionais: ... Riscos Externos: ...",
                        "chart_data": None # Example where chart is optional/not generated
                    },
                    "projecoes_recomendacoes": {
                         "3.1": { "text": "Projeta-se crescimento de 3% na receita...", "chart_data": None },
                         "3.2": { "text": "1. Diversificar Receitas... 2. Fortalecer Controles...", "chart_data": None } # No chart defined for 3.2
                    },
                    "conclusao": {
                        "text": "O município apresenta boa execução orçamentária geral, mas precisa diversificar receitas e melhorar a execução em áreas de menor desempenho.",
                        "chart_data": None
                    }
                }
            ]
        }
    }

# Example of how to generate the JSON schema:
if __name__ == "__main__":
    import json
    schema = AnalysisResponse.model_json_schema()
    print(json.dumps(schema, indent=2, ensure_ascii=False)) 