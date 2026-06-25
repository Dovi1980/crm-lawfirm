"""
Catálogo de templates para redacción asistida por IA.

Cada template declara:
- una clave estable (se persiste en `documents.template_key`)
- nombre y descripción para el picker en UI
- una lista de variables que el usuario debe completar antes de generar
- una instrucción específica para el modelo que se concatena al system prompt

El cuerpo final del documento lo genera el modelo combinando: contexto del
expediente + variables del usuario + instrucción del template. No se usan
plantillas con `{{placeholder}}` para preservar el tono y la flexibilidad.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


VariableType = Literal["text", "textarea", "money", "date"]


@dataclass(frozen=True)
class TemplateVariable:
    key: str
    label: str
    type: VariableType = "text"
    required: bool = True
    placeholder: str = ""
    help: str = ""


@dataclass(frozen=True)
class DocumentTemplate:
    key: str
    name: str
    description: str
    instruction: str  # se inyecta al system prompt
    variables: list[TemplateVariable] = field(default_factory=list)
    default_title: str = ""


TEMPLATES: dict[str, DocumentTemplate] = {
    "carta_documento": DocumentTemplate(
        key="carta_documento",
        name="Carta documento",
        description="Notificación fehaciente — formato Correo Argentino.",
        default_title="Carta documento",
        instruction=(
            "Redactá una CARTA DOCUMENTO en formato argentino. "
            "Estructura obligatoria: encabezado con remitente y destinatario, "
            "cuerpo enumerado en párrafos cortos, intimación clara, plazo legal, "
            "apercibimiento, lugar y fecha, cierre. Tono formal, lenguaje jurídico "
            "directo. No uses fórmulas extranjeras."
        ),
        variables=[
            TemplateVariable(
                "destinatario", "Destinatario (nombre y domicilio)",
                type="textarea",
                placeholder="Juan Pérez — Av. Corrientes 1234, CABA",
            ),
            TemplateVariable(
                "motivo", "Motivo de la intimación",
                type="textarea",
                placeholder="Falta de pago de honorarios pactados por el contrato del 12/03/2025…",
            ),
            TemplateVariable(
                "exigencia", "Qué se exige y plazo",
                type="textarea",
                placeholder="Pago de la suma de $X dentro de las 48 horas hábiles…",
            ),
            TemplateVariable(
                "apercibimiento", "Apercibimiento",
                type="textarea",
                required=False,
                placeholder="Bajo apercibimiento de iniciar acciones legales…",
            ),
        ],
    ),

    "intimacion_cobro": DocumentTemplate(
        key="intimacion_cobro",
        name="Intimación de cobro extrajudicial",
        description="Carta de intimación de pago previa a vía judicial.",
        default_title="Intimación de cobro",
        instruction=(
            "Redactá una INTIMACIÓN DE COBRO EXTRAJUDICIAL en español rioplatense. "
            "Empezá con encabezado profesional, identificá la deuda con monto y "
            "concepto, fundamentá el reclamo en los hechos del expediente, otorgá "
            "un plazo para regularizar y cerrá con la advertencia de acción judicial. "
            "Mencioná intereses si corresponde. Cita de normas: solamente si están "
            "en el dossier; nunca inventes artículos."
        ),
        variables=[
            TemplateVariable(
                "deudor", "Deudor",
                placeholder="Nombre completo o razón social",
            ),
            TemplateVariable(
                "monto", "Monto adeudado",
                type="money",
                placeholder="350000",
            ),
            TemplateVariable(
                "concepto", "Concepto de la deuda",
                type="textarea",
                placeholder="Honorarios facturados según factura B-0001-00012345…",
            ),
            TemplateVariable(
                "plazo_dias", "Plazo otorgado (días hábiles)",
                placeholder="10",
            ),
        ],
    ),

    "escrito_presentacion": DocumentTemplate(
        key="escrito_presentacion",
        name="Escrito de presentación judicial",
        description="Esqueleto de escrito procesal para presentar en autos.",
        default_title="Escrito de presentación",
        instruction=(
            "Redactá un ESCRITO PROCESAL para presentar en autos judiciales "
            "argentinos. Estructura: SUMA / Sr. Juez / cuerpo dividido en romanos "
            "(I. Personería / II. Objeto / III. Hechos / IV. Derecho / V. Prueba / "
            "VI. Petitorio). Mantené un tono respetuoso y técnico. NO inventes "
            "carátulas, números de expediente ni juzgados — usá los del dossier "
            "si están disponibles, sino dejá marcadores `[A COMPLETAR]`."
        ),
        variables=[
            TemplateVariable(
                "objeto", "Objeto de la presentación",
                type="textarea",
                placeholder="Contestación de demanda / Pedido de medida cautelar / Recurso de apelación…",
            ),
            TemplateVariable(
                "petitorio", "Qué se solicita al tribunal",
                type="textarea",
                placeholder="Tenga por presentado el escrito, ordene la medida solicitada…",
            ),
            TemplateVariable(
                "argumentos_clave", "Argumentos clave",
                type="textarea",
                required=False,
                placeholder="Puntos que el modelo debe enfatizar en el desarrollo",
            ),
        ],
    ),

    "convenio_honorarios": DocumentTemplate(
        key="convenio_honorarios",
        name="Convenio de honorarios profesionales",
        description="Acuerdo de honorarios con el cliente, breve y firmable.",
        default_title="Convenio de honorarios",
        instruction=(
            "Redactá un CONVENIO DE HONORARIOS PROFESIONALES entre el estudio y "
            "el cliente del expediente. Cláusulas mínimas: partes, objeto del "
            "patrocinio, alcance, monto, forma de pago, gastos a cargo del cliente, "
            "rescisión, jurisdicción. Tono claro y vinculante. Dos firmas al final."
        ),
        variables=[
            TemplateVariable(
                "alcance", "Alcance del patrocinio",
                type="textarea",
                placeholder="Defensa en juicio caratulado X hasta sentencia de primera instancia…",
            ),
            TemplateVariable(
                "honorarios", "Honorarios pactados",
                type="textarea",
                placeholder="Monto fijo / porcentaje sobre lo obtenido / esquema mixto…",
            ),
            TemplateVariable(
                "forma_pago", "Forma de pago",
                type="textarea",
                placeholder="50% al inicio, 50% al dictarse sentencia favorable…",
            ),
            TemplateVariable(
                "jurisdiccion", "Jurisdicción para conflictos",
                required=False,
                placeholder="Tribunales ordinarios de la Ciudad de Buenos Aires",
            ),
        ],
    ),
}


def list_templates() -> list[DocumentTemplate]:
    return list(TEMPLATES.values())


def get_template(key: str) -> DocumentTemplate | None:
    return TEMPLATES.get(key)


def render_user_inputs_block(template: DocumentTemplate, values: dict[str, str]) -> str:
    """Build a human-readable list of the variables the user filled in."""
    lines = ["## Datos provistos por el abogado"]
    for var in template.variables:
        v = (values.get(var.key) or "").strip()
        if not v:
            if var.required:
                lines.append(f"- **{var.label}**: [SIN DATOS — el modelo debe omitir o marcar como pendiente]")
            continue
        lines.append(f"- **{var.label}**: {v}")
    return "\n".join(lines)
