from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from src.models.database import get_session
from src.models.models import Document, Mention
from src.models.document_enums import DocumentType
from src.api.schemas import (
    DocumentCreateRequest, DocumentUpdateRequest, DocumentResponse
)
from src.api.dependencies import verify_api_key
from src.services.mention_service import create_mentions_for_document

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"], dependencies=[Depends(verify_api_key)])

@router.post("", response_model=DocumentResponse,
    summary="Create a document",
    description="Create a new document with automatic @mention detection")
def create_document(
    request: DocumentCreateRequest,
    author_id: str = Query(..., description="Agent ID of the author"),
    db: Session = Depends(get_session)
):
    try:
        # Validate content length
        if len(request.content) > 50000:  # 50KB limit
            raise HTTPException(
                status_code=400,
                detail="Document content exceeds maximum length of 50,000 characters"
            )
        
        # Ensure content is valid UTF-8
        try:
            request.content.encode('utf-8')
        except UnicodeEncodeError:
            raise HTTPException(
                status_code=400,
                detail="Document content contains invalid characters. Please ensure all text is valid UTF-8."
            )
        
        # Create document
        document = Document(
            doc_type=request.doc_type,
            author_id=author_id,
            title=request.title,
            content=request.content,
            meta_data=request.meta_data,
            expires_at=request.expires_at
        )
        db.add(document)
        db.commit()
        db.refresh(document)
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        db.rollback()
        # Log the error for debugging
        import traceback
        error_detail = f"Failed to create document: {str(e)}"
        traceback_str = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=f"{error_detail}. Please check if your content contains valid UTF-8 characters and try again."
        )
    
    # Extract and create mentions
    mentions = create_mentions_for_document(
        db, document.id, request.content, author_id
    )
    db.commit()
    
    # Prepare response with mentioned agents
    mentioned_agents = [m.mentioned_agent_id for m in mentions]
    
    return DocumentResponse(
        id=document.id,
        doc_type=document.doc_type,
        author_id=document.author_id,
        title=document.title,
        content=document.content,
        meta_data=document.meta_data,
        created_at=document.created_at,
        updated_at=document.updated_at,
        expires_at=document.expires_at,
        mentions=mentioned_agents
    )

@router.get("", response_model=List[DocumentResponse],
    summary="List documents",
    description="List documents by type, with optional filtering")
def list_documents(
    doc_type: Optional[DocumentType] = Query(None, description="Filter by document type"),
    author_id: Optional[str] = Query(None, description="Filter by author"),
    limit: int = Query(1000, description="Maximum number of documents to return"),
    db: Session = Depends(get_session)
):
    query = select(Document)
    
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if author_id:
        query = query.where(Document.author_id == author_id)
    
    # Order by creation date descending
    query = query.order_by(Document.created_at.desc()).limit(limit)
    
    documents = db.exec(query).all()
    
    # Add mentions to each document
    responses = []
    for doc in documents:
        mentions = db.exec(
            select(Mention).where(Mention.document_id == doc.id)
        ).all()
        mentioned_agents = [m.mentioned_agent_id for m in mentions]
        
        responses.append(DocumentResponse(
            id=doc.id,
            doc_type=doc.doc_type,
            author_id=doc.author_id,
            title=doc.title,
            content=doc.content,
            meta_data=doc.meta_data,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            expires_at=doc.expires_at,
            mentions=mentioned_agents
        ))
    
    return responses

@router.get("/{document_id}", response_model=DocumentResponse,
    summary="Get document",
    description="Get a specific document by ID")
def get_document(document_id: int, db: Session = Depends(get_session)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found. Please verify the document ID exists.")
    
    # Get mentions
    mentions = db.exec(
        select(Mention).where(Mention.document_id == document.id)
    ).all()
    mentioned_agents = [m.mentioned_agent_id for m in mentions]
    
    return DocumentResponse(
        id=document.id,
        doc_type=document.doc_type,
        author_id=document.author_id,
        title=document.title,
        content=document.content,
        meta_data=document.meta_data,
        created_at=document.created_at,
        updated_at=document.updated_at,
        expires_at=document.expires_at,
        mentions=mentioned_agents
    )

@router.put("/{document_id}", response_model=DocumentResponse,
    summary="Update document",
    description="Update an existing document")
def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    db: Session = Depends(get_session)
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found. Please verify the document ID exists.")
    
    # Update fields if provided
    if request.title is not None:
        document.title = request.title
    if request.content is not None:
        document.content = request.content
        # Re-extract mentions if content changed
        # First delete old mentions
        db.exec(
            select(Mention).where(Mention.document_id == document.id)
        ).all()
        for mention in document.mentions:
            db.delete(mention)
        # Create new mentions
        mentions = create_mentions_for_document(
            db, document.id, request.content, document.author_id
        )
    if request.meta_data is not None:
        document.meta_data = request.meta_data
    
    document.updated_at = datetime.utcnow()
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Get current mentions
    mentions = db.exec(
        select(Mention).where(Mention.document_id == document.id)
    ).all()
    mentioned_agents = [m.mentioned_agent_id for m in mentions]
    
    return DocumentResponse(
        id=document.id,
        doc_type=document.doc_type,
        author_id=document.author_id,
        title=document.title,
        content=document.content,
        meta_data=document.meta_data,
        created_at=document.created_at,
        updated_at=document.updated_at,
        expires_at=document.expires_at,
        mentions=mentioned_agents
    )

@router.delete("/{document_id}",
    summary="Delete document",
    description="Delete a document and its mentions")
def delete_document(document_id: int, db: Session = Depends(get_session)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found. Please verify the document ID exists.")
    
    # Delete mentions first
    for mention in document.mentions:
        db.delete(mention)
    
    # Delete document
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}