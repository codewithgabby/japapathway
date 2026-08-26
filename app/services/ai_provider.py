from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from app.core.config import settings


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generate text using the AI provider.

        Args:
            system_prompt: System instructions for the AI.
            user_prompt: User content/prompt.
            context: Additional context data.
            **kwargs: Provider-specific parameters.

        Returns:
            Generated text as a string.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass


class MockAIProvider(AIProvider):
    """
    Mock AI provider for development and testing.

    Does not call any external API. It returns a predictable
    draft based only on applicant-provided answers.
    """

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:

        context = context or {}

        section_name = context.get("section_name", "Section")
        applicant_answers = context.get("applicant_answers", [])

        answer_texts = []

        for answer in applicant_answers:
            if not isinstance(answer, dict):
                continue

            answer_text = answer.get("answer_text")

            if answer_text:
                answer_texts.append(str(answer_text).strip())

        if answer_texts:
            content = f"[DRAFT - {section_name}]\n\n"
            content += "\n\n".join(answer_texts)
            content += (
                "\n\n"
                "[This is a mock AI draft. "
                "Real AI integration is not configured yet.]"
            )

            return content

        return (
            f"[Mock AI Draft for {section_name}]\n\n"
            "No applicant information was provided for this section."
        )

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-v1"


class OpenAIProvider(AIProvider):
    """
    OpenAI provider.

    The actual OpenAI API integration will be implemented when
    the application is configured to use OpenAI.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(
            settings,
            "OPENAI_API_KEY",
            None
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:

        raise NotImplementedError(
            "OpenAI provider is not yet configured. "
            "Use MockAIProvider for development and testing."
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return getattr(
            settings,
            "OPENAI_MODEL",
            "not-configured"
        )


class AIProviderFactory:
    """Factory responsible for creating the configured AI provider."""

    _providers = {
        "mock": MockAIProvider,
        "openai": OpenAIProvider,
    }

    @staticmethod
    def get_provider(
        provider_name: Optional[str] = None
    ) -> AIProvider:

        name = (
            provider_name
            or getattr(settings, "AI_PROVIDER", "mock")
        )

        provider_class = AIProviderFactory._providers.get(
            name,
            MockAIProvider
        )

        return provider_class()


class AIDocumentService:
    """
    Service that orchestrates AI document generation.

    AI organizes applicant-provided facts but must never
    invent applicant-specific information.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or AIProviderFactory.get_provider()

    async def generate_section(
        self,
        section_data: Dict[str, Any],
        applicant_answers: List[Dict[str, Any]],
        template_guidance: Optional[str] = None,
        section_guidance: Optional[str] = None,
        admin_guidance: Optional[str] = None,
        published_knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> str:

        system_prompt = self._build_system_prompt(
            template_guidance=template_guidance,
            admin_guidance=admin_guidance,
        )

        user_prompt = self._build_user_prompt(
            section_name=section_data.get("name", "Section"),
            section_purpose=section_data.get("purpose", ""),
            section_guidance=section_guidance,
            applicant_answers=applicant_answers,
            published_knowledge=published_knowledge,
        )

        context = {
            "section_name": section_data.get("name", "Section"),
            "applicant_answers": applicant_answers,
            "template_guidance": template_guidance,
            "section_guidance": section_guidance,
            "admin_guidance": admin_guidance,
            "published_knowledge": published_knowledge,
        }

        return await self.provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
        )

    async def regenerate_section(
        self,
        section_data: Dict[str, Any],
        applicant_answers: List[Dict[str, Any]],
        previous_draft: Optional[str] = None,
        instruction: Optional[str] = None,
        template_guidance: Optional[str] = None,
        section_guidance: Optional[str] = None,
        admin_guidance: Optional[str] = None,
        published_knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> str:

        system_prompt = self._build_system_prompt(
            template_guidance=template_guidance,
            admin_guidance=admin_guidance,
        )

        user_prompt = self._build_regeneration_prompt(
            section_name=section_data.get("name", "Section"),
            section_purpose=section_data.get("purpose", ""),
            section_guidance=section_guidance,
            applicant_answers=applicant_answers,
            published_knowledge=published_knowledge,
            previous_draft=previous_draft,
            instruction=instruction,
        )

        context = {
            "section_name": section_data.get("name", "Section"),
            "applicant_answers": applicant_answers,
            "template_guidance": template_guidance,
            "section_guidance": section_guidance,
            "admin_guidance": admin_guidance,
            "published_knowledge": published_knowledge,
            "previous_draft": previous_draft,
            "instruction": instruction,
        }

        return await self.provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
        )

    def _build_system_prompt(
        self,
        template_guidance: Optional[str] = None,
        admin_guidance: Optional[str] = None,
    ) -> str:

        prompt = (
            "You are an immigration document specialist and professional editor.\n"
            "Your job is to transform the applicant's own natural-language answers "
            "into professional, clear, coherent, and well-structured immigration writing.\n\n"

            "============================================================\n"
            "CRITICAL RULES — FACT PRESERVATION\n"
            "============================================================\n"

            "1. APPLICANT FACTS ARE THE ONLY SOURCE OF PERSONAL TRUTH.\n"
            "2. NEVER invent facts, dates, names, institutions, employment, education, "
            "finances, family, travel history, motivations, or future plans.\n"
            "3. NEVER fill missing personal information with plausible assumptions.\n"
            "4. If a required personal fact is missing, FLAG IT as missing information.\n"
            "5. Do NOT search the internet or use external knowledge as applicant facts.\n"
            "6. Do NOT convert general guidance or published knowledge into personal facts.\n"
            "7. Do NOT exaggerate, embellish, or add unsupported claims.\n"
            "8. Do NOT make every applicant sound identical — preserve their unique voice.\n"
            "9. Preserve the applicant's original meaning, facts, and personal motivation.\n"
            "10. Improve grammar, sentence structure, clarity, coherence, and organization.\n\n"

            "============================================================\n"
            "PUBLISHED CONTENT ENGINE KNOWLEDGE\n"
            "============================================================\n"

            "Published knowledge is for STRUCTURE, TERMINOLOGY, and COMPLETENESS guidance ONLY.\n"
            "It must NEVER become an applicant-specific fact.\n"
            "If published knowledge suggests addressing an issue the applicant did not mention, "
            "FLAG IT as missing information instead of inventing it.\n"
        )

        if admin_guidance:
            prompt += f"\n\nADMIN WRITING GUIDANCE:\n{admin_guidance}\n"

        if template_guidance:
            prompt += f"\n\nTEMPLATE GUIDANCE:\n{template_guidance}\n"

        return prompt

    def _build_user_prompt(
        self,
        section_name: str,
        section_purpose: Optional[str] = None,
        section_guidance: Optional[str] = None,
        applicant_answers: List[Dict[str, Any]] = None,
        published_knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> str:

        prompt = f"SECTION: {section_name}\n"

        if section_purpose:
            prompt += f"\nPURPOSE OF THIS SECTION:\n{section_purpose}\n"

        if section_guidance:
            prompt += f"\nSECTION GUIDANCE:\n{section_guidance}\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "LAYER 1: APPLICANT FACTS (SOURCE OF TRUTH)\n"
        prompt += (
            "These are the ONLY facts that may describe "
            "the applicant's personal circumstances.\n"
        )
        prompt += "=" * 60 + "\n"

        if applicant_answers:
            for answer in applicant_answers:
                question = answer.get("question_text", "")
                response = answer.get("answer_text", "")
                ai_guidance = answer.get("ai_guidance", "")

                if response:
                    prompt += f"\nQ: {question}\nA: {response}\n"

                    if ai_guidance:
                        prompt += (
                            f"[AI Guidance for this answer: "
                            f"{ai_guidance}]\n"
                        )
                else:
                    prompt += (
                        f"\nQ: {question}\n"
                        "A: [NO ANSWER PROVIDED — MISSING]\n"
                    )
        else:
            prompt += "\n[No applicant answers provided]\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "LAYER 2: PUBLISHED CONTENT ENGINE KNOWLEDGE (GUIDANCE ONLY)\n"
        prompt += (
            "This is NOT applicant facts. Use for structure, "
            "terminology, and completeness only.\n"
        )
        prompt += "=" * 60 + "\n"

        if published_knowledge:
            for article in published_knowledge:
                title = article.get("title", "Untitled")
                summary = article.get("summary", "")
                content = article.get("content", "")

                prompt += (
                    f"\n--- KNOWLEDGE ARTICLE: {title} ---\n"
                )

                if summary:
                    prompt += f"Summary: {summary}\n"

                if content:
                    truncated = content[:800]
                    prompt += f"Content: {truncated}\n"

                    if len(content) > 800:
                        prompt += "...[truncated]\n"
        else:
            prompt += "\n[No published knowledge provided]\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "GENERATION INSTRUCTIONS\n"
        prompt += "=" * 60 + "\n"

        prompt += (
            "Write a professional draft for this section using ONLY "
            "the applicant facts from LAYER 1.\n\n"

            "Use LAYER 2 (Published Knowledge) ONLY for:\n"
            "- Understanding what this section should accomplish\n"
            "- Knowing what terminology or concepts to reference\n"
            "- Ensuring completeness of the response structure\n\n"

            "NEVER:\n"
            "- Convert published knowledge into applicant-specific facts\n"
            "- Invent information the applicant did not provide\n"
            "- Fill gaps with plausible assumptions\n"
            "- Make unsupported claims about the applicant\n\n"

            "IF the published knowledge suggests addressing something "
            "the applicant did not provide personal information for, "
            "FLAG IT as missing information in your output.\n\n"

            "Write professionally but naturally. "
            "Preserve the applicant's voice and meaning.\n"
        )

        return prompt

    def _build_regeneration_prompt(
        self,
        section_name: str,
        section_purpose: Optional[str] = None,
        section_guidance: Optional[str] = None,
        applicant_answers: List[Dict[str, Any]] = None,
        published_knowledge: Optional[List[Dict[str, Any]]] = None,
        previous_draft: Optional[str] = None,
        instruction: Optional[str] = None,
    ) -> str:

        prompt = f"SECTION: {section_name}\n"

        if section_purpose:
            prompt += f"\nPURPOSE OF THIS SECTION:\n{section_purpose}\n"

        if section_guidance:
            prompt += f"\nSECTION GUIDANCE:\n{section_guidance}\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "LAYER 1: APPLICANT FACTS (SOURCE OF TRUTH)\n"
        prompt += "=" * 60 + "\n"

        if applicant_answers:
            for answer in applicant_answers:
                question = answer.get("question_text", "")
                response = answer.get("answer_text", "")

                if response:
                    prompt += f"\nQ: {question}\nA: {response}\n"
                else:
                    prompt += (
                        f"\nQ: {question}\n"
                        "A: [NO ANSWER PROVIDED — MISSING]\n"
                    )
        else:
            prompt += "\n[No applicant answers provided]\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "LAYER 2: PUBLISHED CONTENT ENGINE KNOWLEDGE (GUIDANCE ONLY)\n"
        prompt += "=" * 60 + "\n"

        if published_knowledge:
            for article in published_knowledge:
                title = article.get("title", "Untitled")
                summary = article.get("summary", "")
                content = article.get("content", "")

                prompt += f"\n--- KNOWLEDGE ARTICLE: {title} ---\n"

                if summary:
                    prompt += f"Summary: {summary}\n"

                if content:
                    truncated = content[:800]
                    prompt += f"Content: {truncated}\n"

                    if len(content) > 800:
                        prompt += "...[truncated]\n"
        else:
            prompt += "\n[No published knowledge provided]\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "LAYER 3: PREVIOUS DRAFT\n"
        prompt += (
            "Reference this for context. Preserve valid content "
            "unless instructed otherwise.\n"
        )
        prompt += "=" * 60 + "\n"

        if previous_draft:
            prompt += f"\n{previous_draft}\n"
        else:
            prompt += "\n[No previous draft]\n"

        prompt += "\n" + "=" * 60 + "\n"
        prompt += "REGENERATION INSTRUCTION\n"
        prompt += "=" * 60 + "\n"

        if instruction:
            prompt += (
                f"\nApply this transformation: {instruction}\n\n"
            )
        else:
            prompt += (
                "\nImprove the draft while preserving "
                "all facts and meaning.\n\n"
            )

        prompt += (
            "Rewrite the draft following the instruction above.\n"
            "Preserve ALL applicant facts and meaning from LAYER 1.\n"
            "Do NOT introduce new facts.\n"
            "Do NOT remove important personal details.\n"
            "Apply the instruction as a transformation, "
            "not as an invitation to create new content.\n"
        )

        return prompt