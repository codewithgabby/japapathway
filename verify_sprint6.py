"""
Sprint 6 Verification Script
Run this after starting the server to test all AI generation endpoints.

Uses MockAIProvider — no paid AI API required.
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8000/api/v1"


async def test_user_auth():
    print("\n Testing User Authentication...")

    async with httpx.AsyncClient() as client:

        # Try login
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "applicant.test@appname.com",
                "password": "TestApplicant123!",
            },
        )

        if response.status_code == 200:
            tokens = response.json()

            print(" Test user logged in")

            return {
                "Authorization": f"Bearer {tokens['access_token']}"
            }

        # Try register
        response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "applicant.test@appname.com",
                "password": "TestApplicant123!",
                "full_name": "Test Applicant",
            },
        )

        if response.status_code in (200, 201):
            tokens = response.json()

            print(" Test user registered")

            return {
                "Authorization": f"Bearer {tokens['access_token']}"
            }

        print(f" User auth failed: {response.status_code}")
        print(response.text)

        return None


async def get_templates(client):
    response = await client.get(
        f"{BASE_URL}/sop/templates"
    )

    if response.status_code != 200:
        print(
            f" Cannot get templates: "
            f"{response.status_code}"
        )
        print(response.text)

        return []

    return response.json()


async def get_existing_document(
    client,
    document_type,
    pathway_id=None,
):
    response = await client.get(
        f"{BASE_URL}/sop/my-documents",
        params={
            "document_type": document_type
        },
    )

    if response.status_code != 200:
        print(
            f" Failed to get existing "
            f"{document_type.upper()} documents: "
            f"{response.status_code}"
        )

        print(response.text)

        return None

    documents = response.json()

    if pathway_id:

        for document in documents:

            if document.get("pathway_id") == pathway_id:
                return document

    return documents[0] if documents else None


async def get_template_detail(
    client,
    template_slug,
):
    response = await client.get(
        f"{BASE_URL}/sop/templates/slug/{template_slug}"
    )

    if response.status_code != 200:
        print(
            f" Failed to get template "
            f"'{template_slug}': "
            f"{response.status_code}"
        )

        print(response.text)

        return None

    return response.json()


async def test_generation_flow(headers):

    print("\n🤖 Testing AI Document Generation Flow...")

    async with httpx.AsyncClient(
        headers=headers
    ) as client:

        # ============================================================
        # 1. GET AVAILABLE TEMPLATES
        # ============================================================

        print("\nGetting available templates...")

        templates = await get_templates(client)

        if not templates:
            print(" No templates available")
            return

        sop_template = next(
            (
                template
                for template in templates
                if template["document_type"].lower() == "sop"
            ),
            None,
        )

        if not sop_template:
            print(" No SOP template found")
            return

        print(
            f"Using template: "
            f"{sop_template['name']}"
        )

        pathway_id = sop_template["pathway_id"]

        # ============================================================
        # 2. CREATE OR REUSE SOP
        # ============================================================

        print("\nCreating SOP document...")

        response = await client.post(
            f"{BASE_URL}/sop/my-documents",
            json={
                "pathway_id": pathway_id,
                "template_id": sop_template["id"],
                "document_type": "sop",
            },
        )

        if response.status_code == 201:

            document = response.json()

            document_id = document["id"]

            print(
                f" Created document: "
                f"{document_id}"
            )

        elif (
            response.status_code == 400
            and "already have an active SOP"
            in response.text
        ):

            print(
                "Active SOP already exists."
            )

            print(
                "Reusing existing SOP for testing..."
            )

            document = await get_existing_document(
                client,
                "sop",
                pathway_id,
            )

            if not document:

                print(
                    " Could not find existing SOP."
                )

                return

            document_id = document["id"]

            print(
                f"Using existing document: "
                f"{document_id}"
            )

        else:

            print(
                f" Failed to create document: "
                f"{response.status_code}"
            )

            print(response.text)

            return

        # ============================================================
        # 3. GET DOCUMENT DETAIL
        # ============================================================

        print("\nGetting document detail...")

        response = await client.get(
            f"{BASE_URL}/sop/my-documents/"
            f"{document_id}"
        )

        if response.status_code != 200:

            print(
                f" Failed to get document: "
                f"{response.status_code}"
            )

            print(response.text)

            return

        detail = response.json()

        print(
            f" Document has "
            f"{len(detail.get('responses', []))} "
            f"questions"
        )

        # ============================================================
        # 4. GET TEMPLATE DETAIL
        # ============================================================

        print("\nGetting template details...")

        template_detail = await get_template_detail(
            client,
            sop_template["slug"],
        )

        if not template_detail:
            return

        sections = template_detail.get(
            "sections",
            []
        )

        if not sections:

            print(
                " No sections in SOP template"
            )

            return

        print("\nAvailable SOP sections:")

        for section in sections:

            print(
                f"   - {section['name']}: "
                f"{section.get('questions_count', 0)} "
                f"questions"
            )

        # ============================================================
        # 5. FIND SECTION WITH QUESTIONS
        # ============================================================

        first_section = None

        for section in sections:

            if section.get("questions_count", 0) > 0:

                first_section = section

                break

        if not first_section:

            print(
                "\n No SOP section contains "
                "questions."
            )

            print(
                "The template data itself appears "
                "to have zero questions."
            )

            print(
                "This is a template/database seed issue, "
                "not an AI generation endpoint issue."
            )

            return

        section_id = first_section["id"]

        print(
            f"\nUsing section: "
            f"{first_section['name']}"
        )

        # ============================================================
        # 6. ANSWER QUESTIONS
        # ============================================================

        questions = first_section.get(
            "questions",
            []
        )

        if not questions:

            print(
                "\nTemplate endpoint does not "
                "include nested questions."
            )

            print(
                "Using document responses instead."
            )

            questions = detail.get(
                "responses",
                []
            )

        print(
            f"\nAnswering questions "
            f"({len(questions)} questions)..."
        )

        answers = []

        for question in questions:

            question_id = question.get(
                "id"
            ) or question.get(
                "question_id"
            )

            if not question_id:
                continue

            answers.append(
                {
                    "question_id": question_id,
                    "answer_text": (
                        "I studied accounting at "
                        "university and have worked "
                        "in finance for three years. "
                        "I chose this program because "
                        "I want to improve my practical "
                        "knowledge in financial management."
                    ),
                }
            )

        if answers:

            response = await client.post(
                f"{BASE_URL}/sop/my-documents/"
                f"{document_id}/responses",
                json={
                    "answers": answers
                },
            )

            if response.status_code == 201:

                print(
                    f" Saved "
                    f"{len(answers)} responses"
                )

            else:

                print(
                    f" Failed to save responses: "
                    f"{response.status_code}"
                )

                print(response.text)

                return

        else:

            print(
                "No question IDs available "
                "to answer."
            )

        # ============================================================
        # 7. GENERATE AI DRAFT
        # ============================================================

        print("\nGenerating AI draft...")

        response = await client.post(
            f"{BASE_URL}/sop/my-documents/"
            f"{document_id}/generate",
            json={
                "section_id": section_id
            },
        )

        if response.status_code == 200:

            result = response.json()

            print(
                f" Generation status: "
                f"{result.get('status')}"
            )

            print(
                f"   Provider: "
                f"{result.get('provider')}"
            )

            print(
                f"   Model: "
                f"{result.get('model')}"
            )

            content = result.get("content")

            if content:

                print(
                    f"   Content length: "
                    f"{len(content)} chars"
                )

                print(
                    f"   Content preview: "
                    f"{content[:200]}..."
                )

            missing = (
                result.get(
                    "missing_information"
                )
                or []
            )

            if missing:

                print(
                    f"   Missing information: "
                    f"{len(missing)}"
                )

                for item in missing[:3]:

                    print(
                        f"     - {item}"
                    )

            warnings = (
                result.get(
                    "warnings"
                )
                or []
            )

            if warnings:

                print(
                    f"   Warnings: "
                    f"{len(warnings)}"
                )

            knowledge_sources = (
                result.get(
                    "knowledge_sources"
                )
                or []
            )

            if knowledge_sources:

                print(
                    f"   Knowledge sources: "
                    f"{len(knowledge_sources)} articles"
                )

            if result.get("draft_id"):

                print(
                    f"   Draft ID: "
                    f"{result['draft_id']}"
                )

            if result.get("draft_version"):

                print(
                    f"   Draft version: "
                    f"{result['draft_version']}"
                )

        else:

            print(
                f" Generation failed: "
                f"{response.status_code}"
            )

            print(response.text)

            return

        # ============================================================
        # 8. GET DRAFTS
        # ============================================================

        print("\nGetting drafts...")

        response = await client.get(
            f"{BASE_URL}/sop/my-documents/"
            f"{document_id}/drafts"
        )

        if response.status_code == 200:

            drafts = response.json()

            print(
                f"Got {len(drafts)} drafts"
            )

            for draft in drafts:

                print(
                    f"   - Draft v"
                    f"{draft['version']}: "
                    f"{draft['section_name']} - "
                    f"{draft.get('generation_status')}"
                )

        else:

            print(
                f" Failed to get drafts: "
                f"{response.status_code}"
            )

            print(response.text)

        # ============================================================
        # 9. REGENERATE
        # ============================================================

        print(
            "\nRegenerating with instruction..."
        )

        response = await client.post(
            f"{BASE_URL}/sop/my-documents/"
            f"{document_id}/regenerate",
            json={
                "section_id": section_id,
                "instruction": (
                    "Make it more concise while "
                    "preserving all facts."
                ),
            },
        )

        if response.status_code == 200:

            result = response.json()

            print(
                f" Regeneration status: "
                f"{result.get('status')}"
            )

            print(
                f"   Draft version: "
                f"{result.get('draft_version')}"
            )

        else:

            print(
                f" Regeneration failed: "
                f"{response.status_code}"
            )

            print(response.text)


async def test_missing_information(headers):

    print(
        "\n Testing Missing Information Detection..."
    )

    async with httpx.AsyncClient(
        headers=headers
    ) as client:

        # ============================================================
        # 1. GET TEMPLATES
        # ============================================================

        templates = await get_templates(client)

        if not templates:

            print(
                " No templates available"
            )

            return

        # ============================================================
        # 2. FIND LOE TEMPLATE
        # ============================================================

        loe_template = next(
            (
                template
                for template in templates
                if template["document_type"].lower()
                == "loe"
            ),
            None,
        )

        if not loe_template:

            print(
                " No LOE template found"
            )

            return

        print(
            f"Using LOE template: "
            f"{loe_template['name']}"
        )

        pathway_id = loe_template[
            "pathway_id"
        ]

        # ============================================================
        # 3. CREATE LOE
        # ============================================================

        print("\nCreating LOE document...")

        response = await client.post(
            f"{BASE_URL}/sop/my-documents",
            json={
                "pathway_id": pathway_id,
                "template_id": loe_template["id"],
                "document_type": "loe",
                "title": "Test Missing Info LOE",
            },
        )

        if response.status_code != 201:

            print(
                f" Failed to create LOE: "
                f"{response.status_code}"
            )

            print(response.text)

            return

        loe_document = response.json()

        loe_id = loe_document["id"]

        print(
            f"Created LOE: "
            f"{loe_id}"
        )

        # ============================================================
        # 4. GET LOE TEMPLATE
        # ============================================================

        print(
            "\nGetting LOE template details..."
        )

        loe_template_detail = (
            await get_template_detail(
                client,
                loe_template["slug"],
            )
        )

        if not loe_template_detail:
            return

        sections = loe_template_detail.get(
            "sections",
            []
        )

        if not sections:

            print(
                " No LOE sections found"
            )

            return

        print("\nAvailable LOE sections:")

        for section in sections:

            print(
                f"   - {section['name']}: "
                f"{section.get('questions_count', 0)} "
                f"questions"
            )

        # ============================================================
        # 5. FIND SECTION WITH QUESTIONS
        # ============================================================

        section_id = None

        for section in sections:

            if section.get(
                "questions_count",
                0
            ) > 0:

                section_id = section["id"]

                print(
                    f"\nUsing section: "
                    f"{section['name']}"
                )

                break

        if not section_id:

            print(
                " No LOE section with questions"
            )

            return

        # ============================================================
        # 6. GENERATE WITHOUT ANSWERS
        # ============================================================

        print(
            "\nGenerating without answers "
            "(should flag missing info)..."
        )

        response = await client.post(
            f"{BASE_URL}/sop/my-documents/"
            f"{loe_id}/generate",
            json={
                "section_id": section_id
            },
        )

        if response.status_code == 200:

            result = response.json()

            print(
                f" Status: "
                f"{result.get('status')}"
            )

            if (
                result.get("status")
                == "needs_clarification"
            ):

                missing_information = (
                    result.get(
                        "missing_information"
                    )
                    or []
                )

                print(
                    f"   Missing information: "
                    f"{len(missing_information)} items"
                )

                for item in missing_information[:3]:

                    print(
                        f"     - {item}"
                    )

            else:

                print(
                    " Expected "
                    "needs_clarification"
                )

        else:

            print(
                f" Failed: "
                f"{response.status_code}"
            )

            print(response.text)


async def main():

    print("=" * 60)

    print(
        "SPRINT 6 VERIFICATION - "
        "AI Document Generation Engine"
    )

    print("=" * 60)

    # Authentication
    user_headers = await test_user_auth()

    if not user_headers:

        print(
            "\n User authentication failed."
        )

        return

    # Main generation flow
    await test_generation_flow(
        user_headers
    )

    # Missing information test
    await test_missing_information(
        user_headers
    )

    print("\n" + "=" * 60)

    print(
        "SPRINT 6 VERIFICATION COMPLETE"
    )

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())