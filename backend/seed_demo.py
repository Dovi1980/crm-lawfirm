"""
Datos de demostración para Lex Studio CRM.

Crea 2 abogados, 5 clientes, 5 expedientes (uno por materia) y varias gestiones
realistas por expediente, para que las funciones de IA (resumen y chat con
contexto) luzcan con datos verosímiles.

Idempotente: si detecta que ya hay expedientes de demo cargados (por número),
no duplica. Correr con:

    docker compose exec backend python seed_demo.py
"""
import asyncio
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.models.client import Client, ClientType
from app.models.case import Case, CaseType, CaseStatus
from app.models.interaction import Interaction, InteractionType
from app.models.task import Task, TaskPriority, TaskStatus
from app.services.auth_service import AuthService


LAWYERS = [
    {
        "email": "pedro@estudio.com",
        "first_name": "Pedro",
        "last_name": "Letrado",
        "password": "PedroLawyer2026!",
    },
    {
        "email": "laura@estudio.com",
        "first_name": "Laura",
        "last_name": "Abogada",
        "password": "LauraLawyer2026!",
    },
]


async def get_or_create_lawyer(db, data) -> User:
    existing = (await db.execute(select(User).where(User.email == data["email"]))).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email=data["email"],
        hashed_password=AuthService.hash_password(data["password"]),
        first_name=data["first_name"],
        last_name=data["last_name"],
        role=UserRole.LAWYER,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def seed():
    async with SessionLocal() as db:
        # Admin como creador de todo
        admin = (await db.execute(select(User).where(User.role == UserRole.ADMIN))).scalars().first()
        if not admin:
            print("No hay admin. Corré primero: python seed_admin.py")
            return

        # Abogados
        pedro = await get_or_create_lawyer(db, LAWYERS[0])
        laura = await get_or_create_lawyer(db, LAWYERS[1])
        await db.commit()

        # Si ya existe EXP demo, no duplicar
        existing_demo = (
            await db.execute(select(Case).where(Case.case_number.like("EXP-DEMO-%")))
        ).scalars().first()
        if existing_demo:
            print("Los datos de demo ya están cargados. No se duplica.")
            return

        today = date.today()
        now = datetime.utcnow()

        # ---- Clientes ----
        clientes_data = [
            dict(first_name="Juan", last_name="Pérez", client_type=ClientType.NATURAL,
                 tax_id="20-28456789-3", email="juan.perez@gmail.com", phone="11-4567-8901",
                 city="CABA", province="Buenos Aires"),
            dict(first_name="María", last_name="Gómez", client_type=ClientType.NATURAL,
                 tax_id="27-31998765-4", email="maria.gomez@hotmail.com", phone="11-3344-5566",
                 city="La Plata", province="Buenos Aires"),
            dict(first_name="Constructora del Sur", last_name="S.R.L.", client_type=ClientType.LEGAL,
                 tax_id="30-71234567-8", email="legales@constructoradelsur.com.ar", phone="11-5000-1234",
                 city="CABA", province="Buenos Aires"),
            dict(first_name="Roberto", last_name="Fernández", client_type=ClientType.NATURAL,
                 tax_id="20-15678234-9", email="rfernandez@yahoo.com.ar", phone="0221-456-7890",
                 city="La Plata", province="Buenos Aires"),
            dict(first_name="Distribuidora Norte", last_name="S.A.", client_type=ClientType.LEGAL,
                 tax_id="30-70987654-3", email="administracion@distnorte.com", phone="11-4888-2020",
                 city="San Isidro", province="Buenos Aires"),
        ]
        clientes = []
        for c in clientes_data:
            obj = Client(is_active=True, **c)
            db.add(obj)
            clientes.append(obj)
        await db.flush()

        # ---- Expedientes + gestiones ----
        # Cada tupla: (datos del caso, lista de gestiones)
        cases_spec = [
            (
                dict(
                    case_number="EXP-DEMO-0001",
                    title="Despido sin causa - Pérez c/ Distribuidora Norte S.A.",
                    case_type=CaseType.LABORAL, status=CaseStatus.EN_PROCESO,
                    client=clientes[0], lawyer=pedro,
                    start_date=today - timedelta(days=60),
                    estimated_close_date=today + timedelta(days=120),
                    agreed_fees=850000,
                    description="Reclamo por despido sin causa. El trabajador prestó servicios 6 años como repositor. Se reclama indemnización por antigüedad, preaviso e integración del mes de despido, más multas de la Ley 24.013.",
                    internal_notes="El cliente tiene recibos de sueldo de los últimos 12 meses. Falta conseguir testigos de los compañeros de trabajo.",
                ),
                [
                    (InteractionType.REUNION, 60, today - timedelta(days=60),
                     "Primera entrevista con el cliente. Relata despido verbal sin telegrama. Se le explica la viabilidad del reclamo y se solicita documentación: recibos de sueldo, constancia de CUIL y datos de la empresa."),
                    (InteractionType.ESCRITO, 30, today - timedelta(days=52),
                     "Se envía telegrama de intimación (art. 11 Ley 24.013) exigiendo aclaración de situación laboral y registración correcta dentro de 48hs."),
                    (InteractionType.LLAMADA, 15, today - timedelta(days=45),
                     "La empresa responde por carta documento negando la relación laboral en negro. Se evalúa iniciar demanda."),
                    (InteractionType.ESCRITO, 90, today - timedelta(days=30),
                     "Se presenta demanda laboral ante el Juzgado de Trabajo. Se ofrece prueba documental, testimonial y pericial contable."),
                    (InteractionType.AUDIENCIA, 45, today - timedelta(days=7),
                     "Audiencia de conciliación (SECLO). La empresa ofrece $400.000 en concepto de acuerdo. El cliente rechaza. Se continúa la vía judicial."),
                ],
            ),
            (
                dict(
                    case_number="EXP-DEMO-0002",
                    title="Divorcio - Gómez c/ Gómez",
                    case_type=CaseType.FAMILIA, status=CaseStatus.EN_PROCESO,
                    client=clientes[1], lawyer=laura,
                    start_date=today - timedelta(days=40),
                    estimated_close_date=today + timedelta(days=60),
                    agreed_fees=500000,
                    description="Divorcio. Hay dos hijos menores (8 y 12 años). Se discute cuidado personal, régimen de comunicación y cuota alimentaria. Existe inmueble ganancial a liquidar.",
                    internal_notes="La relación entre las partes es tensa pero hay disposición a un convenio. Priorizar acuerdo por el bienestar de los menores.",
                ),
                [
                    (InteractionType.REUNION, 75, today - timedelta(days=40),
                     "Entrevista inicial. La clienta busca divorcio y régimen de cuidado personal compartido con residencia principal en su domicilio. Se explica el proceso de divorcio incausado del CCyC."),
                    (InteractionType.ESCRITO, 60, today - timedelta(days=30),
                     "Se redacta y presenta demanda de divorcio con propuesta reguladora: cuidado compartido, cuota alimentaria del 25% de los ingresos del progenitor, y liquidación del inmueble ganancial 50/50."),
                    (InteractionType.EMAIL, 20, today - timedelta(days=18),
                     "El abogado de la contraparte envía contrapropuesta: acepta cuidado compartido pero ofrece cuota del 18%. Se traslada a la clienta."),
                    (InteractionType.REUNION, 45, today - timedelta(days=5),
                     "Reunión con la clienta. Acepta negociar la cuota en 22%. Se prepara convenio regulador para presentar a homologación."),
                ],
            ),
            (
                dict(
                    case_number="EXP-DEMO-0003",
                    title="Cobro de pesos - Estudio c/ Constructora del Sur S.R.L.",
                    case_type=CaseType.COMERCIAL, status=CaseStatus.NUEVO,
                    client=clientes[2], lawyer=pedro,
                    start_date=today - timedelta(days=15),
                    estimated_close_date=today + timedelta(days=180),
                    agreed_fees=1200000,
                    description="Ejecución de facturas impagas por provisión de materiales de construcción. Monto reclamado: $3.500.000 más intereses. Existen facturas conformadas y remitos firmados.",
                    internal_notes="Documentación sólida. Evaluar vía ejecutiva por las facturas conformadas. Verificar solvencia de la deudora antes de avanzar.",
                ),
                [
                    (InteractionType.REUNION, 50, today - timedelta(days=15),
                     "Reunión con el cliente (proveedor). Aporta 8 facturas conformadas impagas y remitos firmados por el deudor. Se analiza la procedencia de la vía ejecutiva."),
                    (InteractionType.ESCRITO, 40, today - timedelta(days=8),
                     "Se envía carta documento intimando el pago de $3.500.000 en 5 días hábiles bajo apercibimiento de ejecución judicial."),
                    (InteractionType.LLAMADA, 25, today - timedelta(days=2),
                     "El deudor llama proponiendo un plan de pagos en 6 cuotas. Se traslada la propuesta al cliente, que la analiza."),
                ],
            ),
            (
                dict(
                    case_number="EXP-DEMO-0004",
                    title="Daños y perjuicios - Fernández c/ Seguros Aurora S.A.",
                    case_type=CaseType.CIVIL, status=CaseStatus.EN_ESPERA,
                    client=clientes[3], lawyer=laura,
                    start_date=today - timedelta(days=90),
                    estimated_close_date=today + timedelta(days=240),
                    agreed_fees=950000,
                    description="Accidente de tránsito. El cliente sufrió lesiones y daños en su vehículo por colisión con culpa de tercero asegurado. Se reclama daño material, lucro cesante, daño moral e incapacidad sobreviniente.",
                    internal_notes="Esperando pericia médica e ingeniería mecánica. La aseguradora reconoció el siniestro pero discute el monto del daño moral.",
                ),
                [
                    (InteractionType.REUNION, 60, today - timedelta(days=90),
                     "Entrevista inicial. El cliente aporta denuncia policial, fotos del accidente, presupuestos de reparación y certificados médicos por traumatismo cervical."),
                    (InteractionType.ESCRITO, 80, today - timedelta(days=70),
                     "Se presenta demanda por daños y perjuicios contra el conductor y su aseguradora (citada en garantía). Se ofrece prueba pericial médica, mecánica y testimonial."),
                    (InteractionType.AUDIENCIA, 40, today - timedelta(days=40),
                     "Audiencia preliminar (art. 360 CPCCN). Se fijan los hechos controvertidos y se ordenan las pericias. La aseguradora reconoce la mecánica del accidente."),
                    (InteractionType.EMAIL, 15, today - timedelta(days=10),
                     "El perito médico solicita estudios complementarios del cliente. Se coordina turno para resonancia."),
                ],
            ),
            (
                dict(
                    case_number="EXP-DEMO-0005",
                    title="Contrato de distribución - Distribuidora Norte S.A.",
                    case_type=CaseType.COMERCIAL, status=CaseStatus.CERRADO,
                    client=clientes[4], lawyer=pedro,
                    start_date=today - timedelta(days=200),
                    estimated_close_date=today - timedelta(days=20),
                    agreed_fees=600000,
                    description="Asesoramiento y redacción de contrato de distribución exclusiva entre la empresa y un fabricante. Incluye cláusulas de exclusividad territorial, metas de venta y resolución.",
                    internal_notes="Trabajo de asesoramiento finalizado. Contrato firmado por ambas partes. Caso cerrado con éxito.",
                ),
                [
                    (InteractionType.REUNION, 90, today - timedelta(days=200),
                     "Reunión con la gerencia. Se relevan las necesidades: contrato de distribución exclusiva por zona, con metas trimestrales y penalidades por incumplimiento."),
                    (InteractionType.ESCRITO, 120, today - timedelta(days=150),
                     "Se redacta el primer borrador del contrato de distribución con cláusulas de exclusividad, plazo de 3 años, metas de venta y mecanismo de resolución anticipada."),
                    (InteractionType.REUNION, 60, today - timedelta(days=90),
                     "Reunión de revisión con ambas partes. Se ajustan las metas de venta y se incorpora una cláusula de arbitraje para resolución de conflictos."),
                    (InteractionType.ESCRITO, 30, today - timedelta(days=25),
                     "Firma del contrato definitivo por ambas partes. Se entrega copia y se cierra el asesoramiento."),
                ],
            ),
        ]

        for case_data, gestiones in cases_spec:
            client = case_data.pop("client")
            lawyer = case_data.pop("lawyer")
            case = Case(
                client_id=client.id,
                assigned_lawyer_id=lawyer.id,
                created_by_id=admin.id,
                **case_data,
            )
            db.add(case)
            await db.flush()

            for tipo, dur, fecha, desc in gestiones:
                inter = Interaction(
                    interaction_type=tipo,
                    description=desc,
                    interaction_date=datetime.combine(fecha, datetime.min.time()) + timedelta(hours=10),
                    duration_minutes=dur,
                    user_id=lawyer.id,
                    case_id=case.id,
                    client_id=client.id,
                )
                db.add(inter)

        # Un par de tareas pendientes para que el dashboard tenga vida
        db.add(Task(
            title="Conseguir testigos del despido de Pérez",
            description="Contactar a 2 ex compañeros de trabajo dispuestos a declarar.",
            priority=TaskPriority.ALTA, status=TaskStatus.PENDIENTE,
            assigned_to_id=pedro.id, created_by_id=admin.id,
            case_id=None, client_id=clientes[0].id,
            due_date=today + timedelta(days=5),
        ))
        db.add(Task(
            title="Presentar convenio regulador - Divorcio Gómez",
            description="Finalizar y presentar a homologación el convenio acordado.",
            priority=TaskPriority.URGENTE, status=TaskStatus.EN_PROGRESO,
            assigned_to_id=laura.id, created_by_id=admin.id,
            case_id=None, client_id=clientes[1].id,
            due_date=today + timedelta(days=2),
        ))

        await db.commit()
        print("=" * 50)
        print("Datos de demo cargados:")
        print(f"  - 2 abogados (pedro@estudio.com / laura@estudio.com)")
        print(f"  - {len(clientes)} clientes")
        print(f"  - {len(cases_spec)} expedientes con gestiones")
        print(f"  - 2 tareas pendientes")
        print("=" * 50)


async def main():
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
