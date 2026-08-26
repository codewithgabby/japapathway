from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.pathway import (
    ImmigrationPathway,
    RoadmapStep,
    PathwayStatus,
)
from app.models.document import (
    DocumentCategory,
    DocumentType,
    PathwayDocumentRequirement,
)
from app.models.sop import (
    DocumentTemplate,
    DocumentTemplateSection,
    DocumentTemplateQuestion,
    DocumentTemplateStatus,
    DocumentType as SOPDocumentType,
    QuestionType,
)
from app.models.content import (
    ContentCategory,
    ContentArticle,
    ContentVersion,
    ContentStatus,
)
from app.core.security import get_password_hash
from app.services.system import SystemService


async def seed_database(db: AsyncSession):
    """Seed database with default data."""

    # Seed admin user
    result = await db.execute(
        select(User).where(User.email == "admin@appname.com")
    )
    admin = result.scalar_one_or_none()

    if not admin:
        admin = User(
            email="admin@appname.com",
            password_hash=get_password_hash("changeme123"),
            full_name="Workspace Admin",
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True,
        )
        db.add(admin)
        await db.flush()
        print("Admin user created")
    else:
        print("Admin user already exists")

    # Seed system configurations
    await SystemService.seed_default_configs(db)
    print("System configurations seeded")

    # Seed feature flags
    await SystemService.seed_default_features(db)
    print("Feature flags seeded")

    # Seed sample pathways
    await seed_sample_pathways(db, str(admin.id))
    print("Sample pathways seeded")

    # Seed document readiness data
    await seed_document_data(db, str(admin.id))
    print("Document readiness data seeded")

    # Seed SOP and LOE templates
    await seed_sop_templates(db, str(admin.id))
    print("SOP and LOE templates seeded")

    # Seed Content Engine data
    await seed_content_engine(db, str(admin.id))
    print(" Content Engine seeded")

    await db.commit()
    print("Database seeding complete")


async def seed_sample_pathways(
    db: AsyncSession,
    admin_id: str,
):
    """Create sample immigration pathways for testing."""

    # Check if sample pathways already exist
    result = await db.execute(
        select(ImmigrationPathway).where(
            ImmigrationPathway.slug.in_([
                "study-permit",
                "express-entry",
                "visitor-visa",
            ]),
            ImmigrationPathway.is_deleted.is_(False),
        )
    )

    existing_pathways = result.scalars().all()

    if existing_pathways:
        print("Sample pathways already exist")
        return

    # ============================================================
    # STUDY PERMIT PATHWAY
    # ============================================================

    study_permit = ImmigrationPathway(
        name="Study Permit",
        slug="study-permit",
        description="Complete roadmap for Canadian study permit application",
        country="Canada",
        category="study",
        status=PathwayStatus.PUBLISHED,
        version=1,
        sort_order=1,
        is_active=True,
        created_by=admin_id,
        updated_by=admin_id,
    )

    db.add(study_permit)
    await db.flush()

    study_permit_steps = [
        {
            "title": "Research Schools",
            "slug": "research-schools",
            "description": (
                "Research and shortlist Canadian designated learning "
                "institutions (DLIs)"
            ),
            "step_order": 1,
            "estimated_duration_days": 28,
            "is_required": True,
        },
        {
            "title": "Choose Program",
            "slug": "choose-program",
            "description": (
                "Select your program of study and verify admission "
                "requirements"
            ),
            "step_order": 2,
            "estimated_duration_days": 14,
            "is_required": True,
        },
        {
            "title": "Prepare Application",
            "slug": "prepare-application",
            "description": (
                "Prepare academic transcripts, recommendation letters, "
                "and statement of purpose"
            ),
            "step_order": 3,
            "estimated_duration_days": 56,
            "is_required": True,
        },
        {
            "title": "Submit Application",
            "slug": "submit-application",
            "description": (
                "Submit your application to the institution and pay "
                "application fees"
            ),
            "step_order": 4,
            "estimated_duration_days": 7,
            "is_required": True,
        },
        {
            "title": "Receive Admission Letter",
            "slug": "receive-admission",
            "description": (
                "Wait for and receive your letter of acceptance "
                "from the institution"
            ),
            "step_order": 5,
            "estimated_duration_days": 84,
            "is_required": True,
        },
        {
            "title": "Pay Tuition Deposit",
            "slug": "pay-tuition",
            "description": (
                "Pay the required tuition deposit to confirm "
                "your enrollment"
            ),
            "step_order": 6,
            "estimated_duration_days": 14,
            "is_required": True,
        },
        {
            "title": "Gather Documents",
            "slug": "gather-documents",
            "description": (
                "Collect all required documents: passport, financial "
                "proof, medical exam"
            ),
            "step_order": 7,
            "estimated_duration_days": 28,
            "is_required": True,
        },
        {
            "title": "Submit Visa Application",
            "slug": "submit-visa",
            "description": (
                "Submit your study permit application to IRCC with "
                "all supporting documents"
            ),
            "step_order": 8,
            "estimated_duration_days": 7,
            "is_required": True,
        },
        {
            "title": "Biometrics Appointment",
            "slug": "biometrics",
            "description": (
                "Attend biometrics appointment at designated location"
            ),
            "step_order": 9,
            "estimated_duration_days": 1,
            "is_required": True,
        },
        {
            "title": "Medical Examination",
            "slug": "medical-exam",
            "description": (
                "Complete medical examination with IRCC-approved physician"
            ),
            "step_order": 10,
            "estimated_duration_days": 14,
            "is_required": False,
        },
        {
            "title": "Wait for Decision",
            "slug": "wait-decision",
            "description": (
                "Wait for IRCC to process your application"
            ),
            "step_order": 11,
            "estimated_duration_days": 112,
            "is_required": True,
        },
        {
            "title": "Receive Visa Decision",
            "slug": "visa-decision",
            "description": (
                "Receive and review your study permit decision from IRCC"
            ),
            "step_order": 12,
            "estimated_duration_days": 7,
            "is_required": True,
        },
    ]

    for step_data in study_permit_steps:
        step = RoadmapStep(
            pathway_id=study_permit.id,
            created_by=admin_id,
            updated_by=admin_id,
            **step_data,
        )
        db.add(step)

    # ============================================================
    # EXPRESS ENTRY PATHWAY
    # ============================================================

    express_entry = ImmigrationPathway(
        name="Express Entry",
        slug="express-entry",
        description=(
            "Complete roadmap for Express Entry permanent residency "
            "application"
        ),
        country="Canada",
        category="pr",
        status=PathwayStatus.PUBLISHED,
        version=1,
        sort_order=2,
        is_active=True,
        created_by=admin_id,
        updated_by=admin_id,
    )

    db.add(express_entry)
    await db.flush()

    express_entry_steps = [
        {
            "title": "Check Eligibility",
            "slug": "check-eligibility",
            "description": (
                "Verify your eligibility for Express Entry using "
                "CRS calculator"
            ),
            "step_order": 1,
            "estimated_duration_days": 2,
            "is_required": True,
        },
        {
            "title": "Language Test",
            "slug": "language-test",
            "description": (
                "Take IELTS or CELPIP English language test"
            ),
            "step_order": 2,
            "estimated_duration_days": 56,
            "is_required": True,
        },
        {
            "title": "ECA Assessment",
            "slug": "eca-assessment",
            "description": (
                "Get your educational credentials assessed by WES "
                "or equivalent"
            ),
            "step_order": 3,
            "estimated_duration_days": 84,
            "is_required": True,
        },
        {
            "title": "Create Express Entry Profile",
            "slug": "create-profile",
            "description": (
                "Create and submit your Express Entry profile online"
            ),
            "step_order": 4,
            "estimated_duration_days": 14,
            "is_required": True,
        },
        {
            "title": "Receive ITA",
            "slug": "receive-ita",
            "description": (
                "Wait for and receive your Invitation to Apply"
            ),
            "step_order": 5,
            "estimated_duration_days": 180,
            "is_required": True,
        },
        {
            "title": "Gather Documents",
            "slug": "gather-documents",
            "description": (
                "Collect all supporting documents: police clearance, "
                "medical, proof of funds"
            ),
            "step_order": 6,
            "estimated_duration_days": 56,
            "is_required": True,
        },
        {
            "title": "Submit PR Application",
            "slug": "submit-pr",
            "description": (
                "Submit your complete permanent residency application"
            ),
            "step_order": 7,
            "estimated_duration_days": 14,
            "is_required": True,
        },
        {
            "title": "Biometrics",
            "slug": "biometrics-ee",
            "description": (
                "Complete biometrics at designated location"
            ),
            "step_order": 8,
            "estimated_duration_days": 1,
            "is_required": True,
        },
        {
            "title": "Medical Exam",
            "slug": "medical-exam-ee",
            "description": (
                "Complete medical examination for PR application"
            ),
            "step_order": 9,
            "estimated_duration_days": 14,
            "is_required": True,
        },
        {
            "title": "Wait for Processing",
            "slug": "wait-processing",
            "description": (
                "Wait for IRCC to process your PR application"
            ),
            "step_order": 10,
            "estimated_duration_days": 365,
            "is_required": True,
        },
        {
            "title": "Receive COPR",
            "slug": "receive-copr",
            "description": (
                "Receive Confirmation of Permanent Residence"
            ),
            "step_order": 11,
            "estimated_duration_days": 14,
            "is_required": True,
        },
    ]

    for step_data in express_entry_steps:
        step = RoadmapStep(
            pathway_id=express_entry.id,
            created_by=admin_id,
            updated_by=admin_id,
            **step_data,
        )
        db.add(step)

    # ============================================================
    # VISITOR VISA PATHWAY
    # ============================================================

    visitor_visa = ImmigrationPathway(
        name="Visitor Visa",
        slug="visitor-visa",
        description=(
            "Complete roadmap for Canadian visitor visa application"
        ),
        country="Canada",
        category="visitor",
        status=PathwayStatus.PUBLISHED,
        version=1,
        sort_order=3,
        is_active=True,
        created_by=admin_id,
        updated_by=admin_id,
    )

    db.add(visitor_visa)
    await db.flush()

    visitor_visa_steps = [
        {
            "title": "Determine Purpose",
            "slug": "determine-purpose",
            "description": (
                "Define the purpose and duration of your visit"
            ),
            "step_order": 1,
            "estimated_duration_days": 2,
            "is_required": True,
        },
        {
            "title": "Check Requirements",
            "slug": "check-requirements",
            "description": (
                "Review visitor visa requirements for your country"
            ),
            "step_order": 2,
            "estimated_duration_days": 7,
            "is_required": True,
        },
        {
            "title": "Gather Documents",
            "slug": "gather-visa-docs",
            "description": (
                "Collect passport, photos, proof of ties, "
                "financial documents"
            ),
            "step_order": 3,
            "estimated_duration_days": 28,
            "is_required": True,
        },
        {
            "title": "Write Invitation Letter",
            "slug": "invitation-letter",
            "description": (
                "Obtain invitation letter from host in Canada "
                "(if applicable)"
            ),
            "step_order": 4,
            "estimated_duration_days": 14,
            "is_required": False,
        },
        {
            "title": "Complete Application",
            "slug": "complete-application",
            "description": (
                "Fill out the visitor visa application form"
            ),
            "step_order": 5,
            "estimated_duration_days": 7,
            "is_required": True,
        },
        {
            "title": "Submit Application",
            "slug": "submit-visitor-app",
            "description": (
                "Submit your application online or at VAC"
            ),
            "step_order": 6,
            "estimated_duration_days": 1,
            "is_required": True,
        },
        {
            "title": "Biometrics",
            "slug": "biometrics-visitor",
            "description": (
                "Attend biometrics appointment"
            ),
            "step_order": 7,
            "estimated_duration_days": 1,
            "is_required": True,
        },
        {
            "title": "Wait for Decision",
            "slug": "wait-visitor-decision",
            "description": (
                "Wait for IRCC to process your application"
            ),
            "step_order": 8,
            "estimated_duration_days": 56,
            "is_required": True,
        },
        {
            "title": "Receive Decision",
            "slug": "receive-visitor-decision",
            "description": (
                "Receive your visitor visa decision"
            ),
            "step_order": 9,
            "estimated_duration_days": 7,
            "is_required": True,
        },
    ]

    for step_data in visitor_visa_steps:
        step = RoadmapStep(
            pathway_id=visitor_visa.id,
            created_by=admin_id,
            updated_by=admin_id,
            **step_data,
        )
        db.add(step)

    await db.flush()

async def seed_document_data(
    db: AsyncSession,
    admin_id: str,
):
    """Seed default document categories, types, and pathway requirements."""

    # ============================================================
    # DOCUMENT CATEGORIES
    # ============================================================

    category_data = [
        {
            "name": "Identity",
            "slug": "identity",
            "description": "Documents used to establish identity and nationality.",
            "sort_order": 1,
        },
        {
            "name": "Education",
            "slug": "education",
            "description": "Academic and educational documents.",
            "sort_order": 2,
        },
        {
            "name": "Financial",
            "slug": "financial",
            "description": "Documents used to demonstrate financial capacity.",
            "sort_order": 3,
        },
        {
            "name": "Employment",
            "slug": "employment",
            "description": "Employment and professional history documents.",
            "sort_order": 4,
        },
        {
            "name": "Immigration",
            "slug": "immigration",
            "description": "Documents related to immigration history and status.",
            "sort_order": 5,
        },
        {
            "name": "Language",
            "slug": "language",
            "description": "Language proficiency and test result documents.",
            "sort_order": 6,
        },
        {
            "name": "Family",
            "slug": "family",
            "description": "Documents establishing family relationships.",
            "sort_order": 7,
        },
        {
            "name": "Travel",
            "slug": "travel",
            "description": "Travel history and related supporting documents.",
            "sort_order": 8,
        },
    ]

    categories_by_slug = {}

    for data in category_data:
        result = await db.execute(
            select(DocumentCategory).where(
                DocumentCategory.slug == data["slug"],
                DocumentCategory.is_deleted.is_(False),
            )
        )

        category = result.scalar_one_or_none()

        if not category:
            category = DocumentCategory(
                **data,
                is_active=True,
                created_by=admin_id,
                updated_by=admin_id,
            )
            db.add(category)
            await db.flush()

        categories_by_slug[data["slug"]] = category

    # ============================================================
    # DOCUMENT TYPES
    # ============================================================

    document_type_data = [
        {
            "category_slug": "identity",
            "name": "Passport",
            "slug": "passport",
            "description": "Valid passport or travel document.",
        },
        {
            "category_slug": "identity",
            "name": "National Identity Document",
            "slug": "national-id",
            "description": "Government-issued national identity document.",
        },
        {
            "category_slug": "education",
            "name": "Academic Transcript",
            "slug": "academic-transcript",
            "description": "Official academic transcript from an educational institution.",
        },
        {
            "category_slug": "education",
            "name": "Degree or Certificate",
            "slug": "degree-certificate",
            "description": "Degree, diploma, certificate, or other educational credential.",
        },
        {
            "category_slug": "education",
            "name": "Letter of Acceptance",
            "slug": "letter-of-acceptance",
            "description": "Official admission or acceptance letter from the educational institution.",
        },
        {
            "category_slug": "financial",
            "name": "Proof of Funds",
            "slug": "proof-of-funds",
            "description": "Documents demonstrating available financial resources.",
        },
        {
            "category_slug": "financial",
            "name": "Bank Statement",
            "slug": "bank-statement",
            "description": "Recent bank statements or other financial account records.",
        },
        {
            "category_slug": "employment",
            "name": "Employment Letter",
            "slug": "employment-letter",
            "description": "Letter confirming current or previous employment.",
        },
        {
            "category_slug": "employment",
            "name": "Employment Reference",
            "slug": "employment-reference",
            "description": "Reference or employment history documentation.",
        },
        {
            "category_slug": "immigration",
            "name": "Police Certificate",
            "slug": "police-certificate",
            "description": "Police clearance or certificate where applicable.",
        },
        {
            "category_slug": "immigration",
            "name": "Immigration Status Document",
            "slug": "immigration-status-document",
            "description": "Document confirming current or previous immigration status.",
        },
        {
            "category_slug": "immigration",
            "name": "Previous Visa or Permit",
            "slug": "previous-visa-permit",
            "description": "Previous visa, permit, or immigration authorization where applicable.",
        },
        {
            "category_slug": "language",
            "name": "Language Test Result",
            "slug": "language-test-result",
            "description": "Official language proficiency test result.",
        },
        {
            "category_slug": "family",
            "name": "Marriage Certificate",
            "slug": "marriage-certificate",
            "description": "Official document establishing a marriage relationship.",
        },
        {
            "category_slug": "family",
            "name": "Birth Certificate",
            "slug": "birth-certificate",
            "description": "Official birth registration or birth certificate.",
        },
        {
            "category_slug": "travel",
            "name": "Travel History",
            "slug": "travel-history",
            "description": "Documents or information supporting previous travel history.",
        },
    ]

    document_types_by_slug = {}

    for data in document_type_data:
        category = categories_by_slug[data["category_slug"]]

        result = await db.execute(
            select(DocumentType).where(
                DocumentType.slug == data["slug"],
                DocumentType.is_deleted.is_(False),
            )
        )

        document_type = result.scalar_one_or_none()

        if not document_type:
            document_type = DocumentType(
                category_id=category.id,
                name=data["name"],
                slug=data["slug"],
                description=data["description"],
                is_active=True,
                created_by=admin_id,
                updated_by=admin_id,
            )
            db.add(document_type)
            await db.flush()

        document_types_by_slug[data["slug"]] = document_type

    # ============================================================
    # FIND EXISTING PATHWAYS
    # ============================================================

    pathway_slugs = [
        "study-permit",
        "express-entry",
        "visitor-visa",
    ]

    result = await db.execute(
        select(ImmigrationPathway).where(
            ImmigrationPathway.slug.in_(pathway_slugs),
            ImmigrationPathway.is_deleted.is_(False),
        )
    )

    pathways = {
        pathway.slug: pathway
        for pathway in result.scalars().all()
    }

    # If the sample pathways have not been created yet, stop here.
    # This prevents invalid foreign-key references.
    if not pathways:
        print("No sample pathways found. Skipping document requirements.")
        return

    # ============================================================
    # PATHWAY DOCUMENT REQUIREMENTS
    #
    # These are starter/demo requirements for Sprint 3 testing.
    # The admin panel remains the source of truth for actual
    # pathway-specific requirements.
    # ============================================================

    pathway_requirements = {
        "study-permit": [
            {
                "document_slug": "passport",
                "is_required": True,
                "instructions": "Make sure your passport information is current and valid.",
                "display_order": 1,
            },
            {
                "document_slug": "academic-transcript",
                "is_required": True,
                "instructions": "Provide your relevant academic transcript.",
                "display_order": 2,
            },
            {
                "document_slug": "degree-certificate",
                "is_required": True,
                "instructions": "Provide your relevant degree, diploma, or certificate.",
                "display_order": 3,
            },
            {
                "document_slug": "letter-of-acceptance",
                "is_required": True,
                "instructions": "Keep your official admission or acceptance letter available.",
                "display_order": 4,
            },
            {
                "document_slug": "proof-of-funds",
                "is_required": True,
                "instructions": "Prepare evidence showing how your studies and stay will be funded.",
                "display_order": 5,
            },
            {
                "document_slug": "language-test-result",
                "is_required": False,
                "instructions": "Add your language test result if applicable to your situation.",
                "display_order": 6,
            },
            {
                "document_slug": "employment-letter",
                "is_required": False,
                "instructions": "Include employment evidence where relevant to your application.",
                "display_order": 7,
            },
        ],
        "express-entry": [
            {
                "document_slug": "passport",
                "is_required": True,
                "instructions": "Make sure your passport information is current and valid.",
                "display_order": 1,
            },
            {
                "document_slug": "language-test-result",
                "is_required": True,
                "instructions": "Keep your valid language test result available.",
                "display_order": 2,
            },
            {
                "document_slug": "academic-transcript",
                "is_required": True,
                "instructions": "Prepare your relevant academic records.",
                "display_order": 3,
            },
            {
                "document_slug": "degree-certificate",
                "is_required": True,
                "instructions": "Prepare evidence of your educational credentials.",
                "display_order": 4,
            },
            {
                "document_slug": "employment-letter",
                "is_required": True,
                "instructions": "Prepare employment documentation supporting your claimed work experience.",
                "display_order": 5,
            },
            {
                "document_slug": "proof-of-funds",
                "is_required": False,
                "instructions": "Prepare financial evidence where applicable to your circumstances.",
                "display_order": 6,
            },
            {
                "document_slug": "police-certificate",
                "is_required": True,
                "instructions": "Prepare police certificates where required.",
                "display_order": 7,
            },
            {
                "document_slug": "travel-history",
                "is_required": False,
                "instructions": "Keep your relevant travel history information available.",
                "display_order": 8,
            },
        ],
        "visitor-visa": [
            {
                "document_slug": "passport",
                "is_required": True,
                "instructions": "Make sure your passport information is current and valid.",
                "display_order": 1,
            },
            {
                "document_slug": "proof-of-funds",
                "is_required": True,
                "instructions": "Prepare evidence showing that you can support yourself during the visit.",
                "display_order": 2,
            },
            {
                "document_slug": "bank-statement",
                "is_required": True,
                "instructions": "Prepare relevant recent financial records.",
                "display_order": 3,
            },
            {
                "document_slug": "employment-letter",
                "is_required": False,
                "instructions": "Include employment evidence where relevant.",
                "display_order": 4,
            },
            {
                "document_slug": "travel-history",
                "is_required": False,
                "instructions": "Keep relevant previous travel information available.",
                "display_order": 5,
            },
            {
                "document_slug": "marriage-certificate",
                "is_required": False,
                "instructions": "Include this where it is relevant to your circumstances.",
                "display_order": 6,
            },
            {
                "document_slug": "birth-certificate",
                "is_required": False,
                "instructions": "Include this where it is relevant to your circumstances.",
                "display_order": 7,
            },
            {
                "document_slug": "previous-visa-permit",
                "is_required": False,
                "instructions": "Include previous immigration documents where relevant.",
                "display_order": 8,
            },
        ],
    }

    # ============================================================
    # CREATE PATHWAY REQUIREMENTS
    # ============================================================

    for pathway_slug, requirements in pathway_requirements.items():
        pathway = pathways.get(pathway_slug)

        if not pathway:
            print(
                f"Pathway '{pathway_slug}' not found. "
                "Skipping its document requirements."
            )
            continue

        for requirement_data in requirements:
            document_type = document_types_by_slug.get(
                requirement_data["document_slug"]
            )

            if not document_type:
                print(
                    f"Document type '{requirement_data['document_slug']}' "
                    "not found. Skipping requirement."
                )
                continue

            # Prevent duplicate pathway/document-type requirements.
            result = await db.execute(
                select(PathwayDocumentRequirement).where(
                    PathwayDocumentRequirement.pathway_id == pathway.id,
                    PathwayDocumentRequirement.document_type_id == document_type.id,
                    PathwayDocumentRequirement.is_deleted.is_(False),
                )
            )

            existing_requirement = result.scalar_one_or_none()

            if existing_requirement:
                continue

            requirement = PathwayDocumentRequirement(
                pathway_id=pathway.id,
                document_type_id=document_type.id,
                is_required=requirement_data["is_required"],
                is_active=True,
                instructions=requirement_data["instructions"],
                display_order=requirement_data["display_order"],
                created_by=admin_id,
                updated_by=admin_id,
            )

            db.add(requirement)

    await db.flush()

async def seed_sop_templates(
    db: AsyncSession,
    admin_id: str,
):
    """Seed default SOP and LOE templates with sections and questions."""

    # ============================================================
    # CHECK IF SOP/LOE TEMPLATES ALREADY EXIST
    # ============================================================

    result = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.is_deleted.is_(False)
        )
    )

    existing_template = result.first()

    if existing_template:
        print("SOP and LOE templates already exist")
        return

    # ============================================================
    # FIND STUDY PERMIT PATHWAY
    # ============================================================

    result = await db.execute(
        select(ImmigrationPathway).where(
            ImmigrationPathway.slug == "study-permit",
            ImmigrationPathway.is_deleted.is_(False),
        )
    )

    study_permit = result.scalar_one_or_none()

    if not study_permit:
        print(
            "Study Permit pathway not found. "
            "Skipping SOP and LOE templates."
        )
        return

    # ============================================================
    # STUDY PERMIT SOP TEMPLATE
    # ============================================================

    sop_template = DocumentTemplate(
        pathway_id=study_permit.id,
        document_type=SOPDocumentType.SOP,
        name="Study Permit SOP",
        slug="study-permit-sop",
        description=(
            "Statement of Purpose for Study Permit application"
        ),
        status=DocumentTemplateStatus.PUBLISHED,
        version=1,
        admin_guidance=(
            "The SOP should clearly explain the applicant's "
            "educational background, choice of program, choice "
            "of Canada, career plans, and ties to home country. "
            "Avoid generic statements."
        ),
        ai_guidance=(
            "Use only applicant-provided information. "
            "Do not fabricate facts. Make the narrative personal, "
            "logical, and professional."
        ),
        is_active=True,
        created_by=admin_id,
        updated_by=admin_id,
    )

    db.add(sop_template)
    await db.flush()

    # ============================================================
    # SOP SECTIONS
    # ============================================================

    sop_sections_data = [
        {
            "name": "Personal Introduction",
            "slug": "personal-introduction",
            "description": "Introduce the applicant's background",
            "purpose": (
                "Introduce the applicant's academic and "
                "professional background."
            ),
            "order_index": 1,
            "admin_guidance": (
                "Keep to one paragraph. Be factual. "
                "Avoid exaggeration."
            ),
            "questions": [
                {
                    "question_text": (
                        "Tell us about yourself and your current situation."
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "help_text": (
                        "Include your current occupation, location, "
                        "and what you're currently doing."
                    ),
                    "placeholder": "I am currently...",
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "What is your highest level of education?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "help_text": (
                        "Mention your degree, institution, "
                        "and year of graduation."
                    ),
                    "placeholder": "I completed my...",
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Educational Background",
            "slug": "educational-background",
            "description": "Academic history and achievements",
            "purpose": (
                "Explain the applicant's educational journey "
                "and how it leads to the chosen program."
            ),
            "order_index": 2,
            "admin_guidance": (
                "Focus on relevance to the chosen program. "
                "Do not list every subject."
            ),
            "questions": [
                {
                    "question_text": (
                        "What did you study previously and why "
                        "did you choose that field?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": "I studied...",
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "How does your previous education relate "
                        "to the program you want to study now?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "My previous education relates to..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Program Choice",
            "slug": "program-choice",
            "description": "Why this specific program",
            "purpose": (
                "Explain why the applicant chose this specific program."
            ),
            "order_index": 3,
            "admin_guidance": (
                "Be specific. Reference course content, "
                "career relevance, and personal interest."
            ),
            "questions": [
                {
                    "question_text": (
                        "Why did you choose this specific program?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "I chose this program because..."
                    ),
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "What modules or courses in this program "
                        "interest you the most?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "I am particularly interested in..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Why Canada",
            "slug": "why-canada",
            "description": "Reasons for choosing Canada",
            "purpose": (
                "Explain why Canada is the right destination "
                "for the applicant."
            ),
            "order_index": 4,
            "admin_guidance": (
                "Avoid generic statements. Be specific about "
                "Canada's education system, opportunities, "
                "and personal reasons."
            ),
            "questions": [
                {
                    "question_text": (
                        "Why did you choose Canada for your studies?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": "I chose Canada because...",
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "What do you know about Canada's "
                        "education system?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "Canada's education system..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Career Plans",
            "slug": "career-plans",
            "description": "Future career goals",
            "purpose": (
                "Explain how this program fits into "
                "the applicant's career plans."
            ),
            "order_index": 5,
            "admin_guidance": (
                "Be realistic. Connect the program to "
                "specific career outcomes."
            ),
            "questions": [
                {
                    "question_text": (
                        "What are your career goals after "
                        "completing this program?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "After completing this program, I plan to..."
                    ),
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "How will this program help you "
                        "achieve those goals?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "This program will help me..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Home Ties",
            "slug": "home-ties",
            "description": "Connections to home country",
            "purpose": (
                "Demonstrate the applicant's ties "
                "to their home country."
            ),
            "order_index": 6,
            "admin_guidance": (
                "Be specific. Mention family, property, "
                "job prospects, and obligations."
            ),
            "questions": [
                {
                    "question_text": (
                        "What ties do you have to your home country?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "My ties to my home country include..."
                    ),
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "What are your plans after completing your studies?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "After my studies, I plan to..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
    ]

    for section_data in sop_sections_data:
        questions = section_data.pop("questions", [])

        section = DocumentTemplateSection(
            template_id=sop_template.id,
            created_by=admin_id,
            updated_by=admin_id,
            **section_data,
        )

        db.add(section)
        await db.flush()

        for question_data in questions:
            question = DocumentTemplateQuestion(
                section_id=section.id,
                created_by=admin_id,
                updated_by=admin_id,
                **question_data,
            )

            db.add(question)

    # ============================================================
    # STUDY PERMIT LOE TEMPLATE
    # ============================================================

    loe_template = DocumentTemplate(
        pathway_id=study_permit.id,
        document_type=SOPDocumentType.LOE,
        name="Study Permit LOE",
        slug="study-permit-loe",
        description=(
            "Letter of Explanation for Study Permit application"
        ),
        status=DocumentTemplateStatus.PUBLISHED,
        version=1,
        admin_guidance=(
            "The LOE should explain specific circumstances "
            "clearly and professionally."
        ),
        ai_guidance=(
            "Use only applicant-provided information. "
            "Be factual and professional."
        ),
        is_active=True,
        created_by=admin_id,
        updated_by=admin_id,
    )

    db.add(loe_template)
    await db.flush()

    # ============================================================
    # LOE SECTIONS
    # ============================================================

    loe_sections_data = [
        {
            "name": "Reason for Explanation",
            "slug": "reason-for-explanation",
            "description": "What this LOE explains",
            "purpose": (
                "Clearly state what this letter explains."
            ),
            "order_index": 1,
            "questions": [
                {
                    "question_text": (
                        "What is the reason for this letter "
                        "of explanation?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": "This letter explains...",
                    "is_required": True,
                    "order_index": 1,
                },
            ],
        },
        {
            "name": "Circumstances",
            "slug": "circumstances",
            "description": "Detailed explanation of circumstances",
            "purpose": (
                "Explain the circumstances in detail."
            ),
            "order_index": 2,
            "questions": [
                {
                    "question_text": (
                        "Please describe the circumstances in detail."
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": "The circumstances are...",
                    "is_required": True,
                    "order_index": 1,
                },
                {
                    "question_text": (
                        "What evidence or context supports "
                        "your explanation?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": (
                        "The supporting context is..."
                    ),
                    "is_required": True,
                    "order_index": 2,
                },
            ],
        },
        {
            "name": "Conclusion",
            "slug": "conclusion",
            "description": "Summary and closing",
            "purpose": (
                "Summarize the explanation and close professionally."
            ),
            "order_index": 3,
            "questions": [
                {
                    "question_text": (
                        "What would you like the visa officer "
                        "to understand from this explanation?"
                    ),
                    "question_type": QuestionType.LONG_TEXT,
                    "placeholder": "I hope this explains...",
                    "is_required": True,
                    "order_index": 1,
                },
            ],
        },
    ]

    for section_data in loe_sections_data:
        questions = section_data.pop("questions", [])

        section = DocumentTemplateSection(
            template_id=loe_template.id,
            created_by=admin_id,
            updated_by=admin_id,
            **section_data,
        )

        db.add(section)
        await db.flush()

        for question_data in questions:
            question = DocumentTemplateQuestion(
                section_id=section.id,
                created_by=admin_id,
                updated_by=admin_id,
                **question_data,
            )

            db.add(question)

    await db.flush()

    print("SOP and LOE templates with sections and questions seeded")

async def seed_content_engine(db: AsyncSession, admin_id: str):
    """Create sample content categories and articles for Content Engine."""
    
    # Check if already seeded
    result = await db.execute(
        select(ContentCategory).where(ContentCategory.is_deleted == False)
    )
    existing = result.first()
    if existing:
        print("Content Engine categories already exist")
        return
    
    # Get pathways
    result = await db.execute(
        select(ImmigrationPathway).where(ImmigrationPathway.is_deleted == False)
    )
    pathways = {p.slug: p for p in result.scalars().all()}
    
    study_permit = pathways.get("study-permit")
    visitor_visa = pathways.get("visitor-visa")
    express_entry = pathways.get("express-entry")
    
    if not study_permit:
        print("Study Permit pathway not found. Skipping Content Engine seed.")
        return
    
    # ============================================================
    # CONTENT CATEGORIES
    # ============================================================
    
    categories_data = [
        {
            "name": "Purpose of Visit",
            "slug": "purpose-of-visit",
            "description": "Guidance on explaining the purpose of visit in immigration applications.",
        },
        {
            "name": "Proof of Funds",
            "slug": "proof-of-funds",
            "description": "Guidance on demonstrating financial capacity for immigration applications.",
        },
        {
            "name": "Home Ties",
            "slug": "home-ties",
            "description": "Guidance on demonstrating ties to home country.",
        },
        {
            "name": "Study Plan",
            "slug": "study-plan",
            "description": "Guidance on explaining study plans and academic goals.",
        },
        {
            "name": "Common Mistakes",
            "slug": "common-mistakes",
            "description": "Common mistakes to avoid in immigration applications.",
        },
        {
            "name": "Writing Guidance",
            "slug": "writing-guidance",
            "description": "Guidance on professional writing for immigration documents.",
        },
    ]
    
    category_map = {}
    for cat_data in categories_data:
        category = ContentCategory(
            **cat_data,
            status=ContentStatus.PUBLISHED,
            version=1,
            is_active=True,
            created_by=admin_id,
            updated_by=admin_id
        )
        db.add(category)
        await db.flush()
        category_map[cat_data["slug"]] = category
    
    # ============================================================
    # CONTENT ARTICLES
    # ============================================================
    
    articles_data = [
        # Study Permit - Purpose of Visit
        {
            "category_slug": "purpose-of-visit",
            "pathway_slug": "study-permit",
            "title": "How to Explain Your Purpose of Visit for Study Permit",
            "slug": "study-permit-purpose-of-visit",
            "summary": "Learn how to clearly explain why you want to study in Canada.",
            "content": (
                "Your purpose of visit explanation should be specific and personal. "
                "Avoid generic statements like 'I want to study abroad for better opportunities.' "
                "Instead, explain what specific program you chose, why you chose it, and how it "
                "connects to your previous education and future career goals.\n\n"
                "Key points to address:\n"
                "1. What specific program you want to study\n"
                "2. Why you chose this program\n"
                "3. Why you chose this institution\n"
                "4. How this program relates to your background\n"
                "5. What you plan to do after completing the program"
            ),
        },
        {
            "category_slug": "purpose-of-visit",
            "pathway_slug": "visitor-visa",
            "title": "How to Explain Your Purpose of Visit for Visitor Visa",
            "slug": "visitor-visa-purpose-of-visit",
            "summary": "Learn how to clearly explain why you want to visit Canada temporarily.",
            "content": (
                "For a visitor visa, your purpose of visit must be clear and temporary. "
                "Explain what you plan to do, how long you will stay, and why you will return home.\n\n"
                "Key points to address:\n"
                "1. The specific reason for your visit\n"
                "2. Duration of your stay\n"
                "3. Who you are visiting (if applicable)\n"
                "4. Your ties to your home country\n"
                "5. Your ability to fund the trip"
            ),
        },
        # Study Permit - Home Ties
        {
            "category_slug": "home-ties",
            "pathway_slug": "study-permit",
            "title": "How to Demonstrate Home Ties for Study Permit",
            "slug": "study-permit-home-ties",
            "summary": "Guidance on proving you will return to your home country after studies.",
            "content": (
                "Demonstrating home ties is critical for study permit approval. "
                "Visa officers need to believe you will leave Canada after your studies.\n\n"
                "Strong home ties include:\n"
                "1. Family obligations (spouse, children, elderly parents)\n"
                "2. Property ownership\n"
                "3. Current employment or job offer waiting for you\n"
                "4. Business ownership\n"
                "5. Strong community connections\n\n"
                "Be specific. Instead of saying 'I have family,' say 'I live with my parents and "
                "help care for my younger siblings. I am expected to return to continue supporting them.'"
            ),
        },
        # Study Permit - Proof of Funds
        {
            "category_slug": "proof-of-funds",
            "pathway_slug": "study-permit",
            "title": "How to Explain Proof of Funds for Study Permit",
            "slug": "study-permit-proof-of-funds",
            "summary": "Guidance on demonstrating you can financially support your studies.",
            "content": (
                "You must prove you have enough money to cover tuition and living expenses "
                "for at least your first year in Canada.\n\n"
                "Acceptable proof includes:\n"
                "1. Bank statements showing sufficient balance\n"
                "2. Scholarship or funding letters\n"
                "3. Education loan approval\n"
                "4. Sponsor's financial documents\n\n"
                "If someone else is funding your studies, explain their relationship to you "
                "and why they are willing to support you."
            ),
        },
        # Study Permit - Writing Guidance
        {
            "category_slug": "writing-guidance",
            "pathway_slug": "study-permit",
            "title": "Writing Guidance for Study Permit SOP",
            "slug": "study-permit-writing-guidance",
            "summary": "Professional writing standards for study permit statements.",
            "content": (
                "Your Statement of Purpose should be professional, clear, and honest.\n\n"
                "Writing tips:\n"
                "1. Use first person ('I')\n"
                "2. Be specific — avoid vague statements\n"
                "3. Use formal but natural language\n"
                "4. Organize your ideas logically\n"
                "5. Proofread for grammar and spelling\n"
                "6. Keep it between 1-2 pages\n\n"
                "Avoid:\n"
                "1. Generic statements about 'quality education'\n"
                "2. Copying templates from the internet\n"
                "3. Exaggerating your achievements\n"
                "4. Making unsupported claims"
            ),
        },
        # Common Mistakes
        {
            "category_slug": "common-mistakes",
            "pathway_slug": "study-permit",
            "title": "Common SOP Mistakes to Avoid",
            "slug": "study-permit-common-mistakes",
            "summary": "Learn what to avoid when writing your study permit SOP.",
            "content": (
                "Common mistakes that weaken study permit applications:\n\n"
                "1. Being too generic — 'Canada has great education'\n"
                "2. Not explaining why you chose Canada specifically\n"
                "3. No clear connection between your past education and chosen program\n"
                "4. Vague career plans\n"
                "5. Not addressing potential concerns (study gaps, career changes)\n"
                "6. Contradicting information elsewhere in your application\n"
                "7. Copying sample SOPs from the internet"
            ),
        },
    ]
    
    for article_data in articles_data:
        category = category_map.get(article_data["category_slug"])
        pathway = pathways.get(article_data["pathway_slug"])
        
        if not category or not pathway:
            continue
        
        article = ContentArticle(
            category_id=category.id,
            pathway_id=pathway.id,
            title=article_data["title"],
            slug=article_data["slug"],
            summary=article_data["summary"],
            content=article_data["content"],
            status=ContentStatus.PUBLISHED,
            version=1,
            is_active=True,
            created_by=admin_id,
            updated_by=admin_id
        )
        db.add(article)
        await db.flush()
        
        # Create version 1
        version = ContentVersion(
            article_id=article.id,
            version=1,
            title=article.title,
            summary=article.summary,
            content=article.content,
            status=ContentStatus.PUBLISHED,
            created_by=admin_id
        )
        db.add(version)
    
    await db.flush()
    print("Seeded 6 content categories and 7 content articles")
        