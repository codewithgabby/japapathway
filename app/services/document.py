# app/services/document.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.models.document import (
    DocumentCategory,
    DocumentType,
    PathwayDocumentRequirement,
    UserDocumentChecklist
)
from app.services.pathway import PathwayService
from app.core.exceptions import NotFoundException, BadRequestException


class DocumentService:
    
    # ========== Admin: Category CRUD ==========
    
    @staticmethod
    async def create_category(db: AsyncSession, data: dict, user_id: str) -> DocumentCategory:
        result = await db.execute(
            select(DocumentCategory).where(
                DocumentCategory.slug == data["slug"],
                DocumentCategory.is_deleted.is_(False)
            )
        )
        if result.scalar_one_or_none():
            raise BadRequestException("Category with this slug already exists")
        
        category = DocumentCategory(
            **data,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def get_category(db: AsyncSession, category_id: str) -> DocumentCategory:
        result = await db.execute(
            select(DocumentCategory).where(
                DocumentCategory.id == category_id,
                DocumentCategory.is_deleted.is_(False)
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException("Document category")
        return category
    
    @staticmethod
    async def get_all_categories(
        db: AsyncSession, include_inactive: bool = False
    ) -> List[DocumentCategory]:
        query = select(DocumentCategory).where(DocumentCategory.is_deleted.is_(False))
        if not include_inactive:
            query = query.where(DocumentCategory.is_active.is_(True))
        query = query.order_by(DocumentCategory.sort_order)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_category(
        db: AsyncSession, category_id: str, data: dict, user_id: str
    ) -> DocumentCategory:
        category = await DocumentService.get_category(db, category_id)
        
        if "slug" in data and data["slug"] != category.slug:
            result = await db.execute(
                select(DocumentCategory).where(
                    DocumentCategory.slug == data["slug"],
                    DocumentCategory.id != category_id,
                    DocumentCategory.is_deleted.is_(False)
                )
            )
            if result.scalar_one_or_none():
                raise BadRequestException("Category with this slug already exists")
        
        for key, value in data.items():
            setattr(category, key, value)
        
        category.updated_by = user_id
        await db.flush()
        return category
    
    @staticmethod
    async def delete_category(
        db: AsyncSession,
        category_id: str,
        user_id: str
    ) -> None:
        category = await DocumentService.get_category(
            db,
            category_id
        )

        category.soft_delete(user_id)

        await db.commit()
    
    # ========== Admin: Document Type CRUD ==========
    
    @staticmethod
    async def create_document_type(db: AsyncSession, data: dict, user_id: str) -> DocumentType:
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.slug == data["slug"],
                DocumentType.is_deleted.is_(False)
            )
        )
        if result.scalar_one_or_none():
            raise BadRequestException("Document type with this slug already exists")
        
        # Validate category exists
        await DocumentService.get_category(db, data["category_id"])
        
        document_type = DocumentType(
            **data,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(document_type)
        await db.commit()
        await db.refresh(document_type)
        return document_type
    
    @staticmethod
    async def get_document_type(db: AsyncSession, document_type_id: str) -> DocumentType:
        result = await db.execute(
            select(DocumentType).where(
                DocumentType.id == document_type_id,
                DocumentType.is_deleted.is_(False)
            )
        )
        document_type = result.scalar_one_or_none()
        if not document_type:
            raise NotFoundException("Document type")
        return document_type
    
    @staticmethod
    async def get_all_document_types(
        db: AsyncSession, category_id: Optional[str] = None, include_inactive: bool = False
    ) -> List[DocumentType]:
        query = select(DocumentType).where(DocumentType.is_deleted.is_(False))
        if category_id:
            query = query.where(DocumentType.category_id == category_id)
        if not include_inactive:
            query = query.where(DocumentType.is_active.is_(True))
        query = query.order_by(DocumentType.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_document_type(
        db: AsyncSession,
        document_type_id: str,
        data: dict,
        user_id: str
    ) -> DocumentType:

        document_type = await DocumentService.get_document_type(
            db,
            document_type_id
        )

        if "slug" in data and data["slug"] != document_type.slug:
            result = await db.execute(
                select(DocumentType).where(
                    DocumentType.slug == data["slug"],
                    DocumentType.id != document_type_id,
                    DocumentType.is_deleted.is_(False)
                )
            )

            if result.scalar_one_or_none():
                raise BadRequestException(
                    "Document type with this slug already exists"
                )

        if "category_id" in data and data["category_id"] != str(
            document_type.category_id
        ):
            await DocumentService.get_category(
                db,
                data["category_id"]
            )

        for key, value in data.items():
            setattr(document_type, key, value)

        document_type.updated_by = user_id

        await db.commit()
        await db.refresh(document_type)

        return document_type
    
    @staticmethod
    async def delete_document_type(
        db: AsyncSession,
        document_type_id: str,
        user_id: str
    ) -> None:
        document_type = await DocumentService.get_document_type(
            db,
            document_type_id
        )

        document_type.soft_delete(user_id)

        await db.commit()
    
    # ========== Admin: Pathway Requirement CRUD ==========
    
    @staticmethod
    async def add_requirement(
        db: AsyncSession, data: dict, user_id: str
    ) -> PathwayDocumentRequirement:
        # Validate pathway
        await PathwayService.get_pathway_by_id(db, data["pathway_id"])
        # Validate document type
        await DocumentService.get_document_type(db, data["document_type_id"])
        
        # Check duplicate
        result = await db.execute(
            select(PathwayDocumentRequirement).where(
                PathwayDocumentRequirement.pathway_id == data["pathway_id"],
                PathwayDocumentRequirement.document_type_id == data["document_type_id"],
                PathwayDocumentRequirement.is_deleted.is_(False)
            )
        )
        if result.scalar_one_or_none():
            raise BadRequestException("Requirement already exists for this pathway")
        
        requirement = PathwayDocumentRequirement(
            **data,
            created_by=user_id,
            updated_by=user_id
        )
        db.add(requirement)

        await db.commit()
        await db.refresh(requirement)

        return requirement
    
    @staticmethod
    async def get_requirement(db: AsyncSession, requirement_id: str) -> PathwayDocumentRequirement:
        result = await db.execute(
            select(PathwayDocumentRequirement).where(
                PathwayDocumentRequirement.id == requirement_id,
                PathwayDocumentRequirement.is_deleted.is_(False)
            )
        )
        requirement = result.scalar_one_or_none()
        if not requirement:
            raise NotFoundException("Document requirement")
        return requirement
    
    @staticmethod
    async def get_pathway_requirements(
        db: AsyncSession, pathway_id: str, include_inactive: bool = False
    ) -> List[PathwayDocumentRequirement]:
        await PathwayService.get_pathway_by_id(db, pathway_id)
        
        query = select(PathwayDocumentRequirement).where(
            PathwayDocumentRequirement.pathway_id == pathway_id,
            PathwayDocumentRequirement.is_deleted.is_(False)
        )
        if not include_inactive:
            query = query.where(PathwayDocumentRequirement.is_active.is_(True))
        query = query.order_by(PathwayDocumentRequirement.display_order)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_requirement(
        db: AsyncSession, requirement_id: str, data: dict, user_id: str
    ) -> PathwayDocumentRequirement:
        requirement = await DocumentService.get_requirement(db, requirement_id)
        
        for key, value in data.items():
            setattr(requirement, key, value)
        
        requirement.updated_by = user_id

        await db.commit()
        await db.refresh(requirement)

        return requirement
    
    @staticmethod
    async def delete_requirement(db: AsyncSession, requirement_id: str, user_id: str) -> None:
        requirement = await DocumentService.get_requirement(db, requirement_id)
        requirement.soft_delete(user_id)
        await db.commit()
    
    # ========== Applicant: Checklist Logic ==========
    
    @staticmethod
    async def get_or_create_checklist(
        db: AsyncSession, user_id: str, pathway_id: str
    ) -> List[UserDocumentChecklist]:
        """Get existing checklist or create new one from pathway requirements"""
        
        # Check existing
        result = await db.execute(
            select(UserDocumentChecklist).where(
                UserDocumentChecklist.user_id == user_id,
                UserDocumentChecklist.pathway_id == pathway_id,
                UserDocumentChecklist.is_deleted.is_(False)
            )
        )
        existing = result.scalars().all()

        requirements = await DocumentService.get_pathway_requirements(
            db, pathway_id
        )

        if not requirements:
            raise BadRequestException(
                "No document requirements configured for this pathway"
            )

        existing_requirement_ids = {
            str(item.requirement_id)
            for item in existing
        }

        # Add checklist entries for any newly configured requirements
        for req in requirements:
            if str(req.id) not in existing_requirement_ids:
                item = UserDocumentChecklist(
                    user_id=user_id,
                    pathway_id=pathway_id,
                    requirement_id=req.id,
                    status="not_ready"
                )
                db.add(item)
                existing.append(item)

        await db.flush()

        return existing
    
    @staticmethod
    async def get_checklist_with_details(
        db: AsyncSession, user_id: str, pathway_id: str
    ) -> List[Dict[str, Any]]:
        """Get enriched checklist with document info"""
        
        items = await DocumentService.get_or_create_checklist(db, user_id, pathway_id)
        
        enriched = []
        for item in items:
            requirement = await DocumentService.get_requirement(db, str(item.requirement_id))
            document_type = await DocumentService.get_document_type(db, str(requirement.document_type_id))
            category = await DocumentService.get_category(db, str(document_type.category_id))
            
            enriched.append({
                "id": str(item.id),
                "requirement_id": str(item.requirement_id),
                "document_type_id": str(document_type.id),
                "document_name": document_type.name,
                "category_name": category.name,
                "is_required": requirement.is_required,
                "instructions": requirement.instructions,
                "display_order": requirement.display_order,
                "status": item.status,
                "notes": item.notes
            })
        
        # Sort by display order
        enriched.sort(key=lambda x: x["display_order"])
        return enriched
    
    @staticmethod
    async def update_checklist_item(
        db: AsyncSession, user_id: str, pathway_id: str, requirement_id: str, status: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update single checklist item status"""
        
        if status not in ["ready", "not_ready"]:
            raise BadRequestException("Status must be 'ready' or 'not_ready'")
        
        # Validate requirement exists and belongs to this pathway
        requirement = await DocumentService.get_requirement(db, requirement_id)

        if str(requirement.pathway_id) != str(pathway_id):
            raise BadRequestException(
                "Document requirement does not belong to this pathway"
            )

        # Find existing checklist item
        result = await db.execute(
            select(UserDocumentChecklist).where(
                UserDocumentChecklist.user_id == user_id,
                UserDocumentChecklist.pathway_id == pathway_id,
                UserDocumentChecklist.requirement_id == requirement_id,
                UserDocumentChecklist.is_deleted.is_(False)
            )
        )
        item = result.scalar_one_or_none()

        if not item:
            # Auto-create if not exists
            item = UserDocumentChecklist(
                user_id=user_id,
                pathway_id=pathway_id,
                requirement_id=requirement_id,
                status=status,
                notes=notes
            )
            db.add(item)
        else:
            item.status = status
            if notes is not None:
                item.notes = notes
        
        await db.flush()
        await db.commit()
        
        # Return enriched item
        document_type = await DocumentService.get_document_type(
            db, str(requirement.document_type_id)
        )
        category = await DocumentService.get_category(db, str(document_type.category_id))
        
        return {
            "id": str(item.id),
            "requirement_id": str(item.requirement_id),
            "document_type_id": str(document_type.id),
            "document_name": document_type.name,
            "category_name": category.name,
            "is_required": requirement.is_required,
            "instructions": requirement.instructions,
            "display_order": requirement.display_order,
            "status": item.status,
            "notes": item.notes
        }
    
    @staticmethod
    async def get_readiness_summary(
        db: AsyncSession, user_id: str, pathway_id: str
    ) -> Dict[str, Any]:
        """Calculate deterministic readiness summary"""
        
        pathway = await PathwayService.get_pathway_by_id(db, pathway_id)
        items = await DocumentService.get_checklist_with_details(db, user_id, pathway_id)
        
        required_items = [i for i in items if i["is_required"]]
        optional_items = [i for i in items if not i["is_required"]]
        
        total_required = len(required_items)
        completed_required = len([i for i in required_items if i["status"] == "ready"])
        missing_required = total_required - completed_required
        
        total_optional = len(optional_items)
        completed_optional = len([i for i in optional_items if i["status"] == "ready"])
        
        # Percentage based on required documents only
        completion_percentage = int((completed_required / total_required) * 100) if total_required > 0 else 0
        
        missing_documents = [i["document_name"] for i in required_items if i["status"] != "ready"]
        
        # Rule-based recommendations
        recommendations = []
        if missing_required > 0:
            recommendations.append(f"You have {missing_required} required document(s) remaining.")
            if len(missing_documents) <= 3:
                recommendations.append(f"Prioritize completing: {', '.join(missing_documents)}.")
            else:
                top_missing = missing_documents[:3]
                recommendations.append(f"Start with: {', '.join(top_missing)}.")
        else:
            recommendations.append("All required documents are ready. Great job!")
            if total_optional > completed_optional:
                recommendations.append(f"Consider completing {total_optional - completed_optional} optional document(s) to strengthen your application.")
        
        return {
            "pathway_id": str(pathway.id),
            "pathway_name": pathway.name,
            "pathway_slug": pathway.slug,
            "total_required": total_required,
            "completed_required": completed_required,
            "missing_required": missing_required,
            "total_optional": total_optional,
            "completed_optional": completed_optional,
            "completion_percentage": completion_percentage,
            "missing_documents": missing_documents,
            "recommendations": recommendations
        }