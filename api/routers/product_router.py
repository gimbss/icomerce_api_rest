from fastapi import APIRouter, Depends, HTTPException, Query, status
from api.dependencies import get_product_controller, get_current_user_id, get_current_admin_user_id
from api.schemas import (
    CreateProductRequest,
    UpdateProductRequest,
    ProductCreateResponse,
    ProductSingleResponse,
    ProductListResponse,
    ProductDeleteResponse,
    ErrorResponse,
)
from app.controllers.product_controller import ProductController

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def create_product(
    body: CreateProductRequest,
    ctrl: ProductController = Depends(get_product_controller),
    _admin_id: int = Depends(get_current_admin_user_id),
):
    ''' Criar um novo produto. Apenas administradores podem criar produtos. '''
    result = ctrl.create_product(
        name=body.name,
        description=body.description,
        price=body.price,
        category=body.category,
        stock=body.stock,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.get(
    "",
    response_model=ProductListResponse,
    responses={401: {"model": ErrorResponse}},
)
def list_products(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
    ctrl: ProductController = Depends(get_product_controller),
    _user_id: int = Depends(get_current_user_id),
):
    ''' Obter a lista de todos os produtos disponíveis com paginação. '''
    result = ctrl.list_products(skip=skip, limit=limit)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.get(
    "/{product_id}",
    response_model=ProductSingleResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_product(
    product_id: int,
    ctrl: ProductController = Depends(get_product_controller),
    _user_id: int = Depends(get_current_user_id),
):
    ''' Obter os detalhes de um produto específico. '''
    result = ctrl.get_product_by_id(product_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result

@router.get(
    "/category/{category}",
    response_model=ProductListResponse,
    responses={401: {"model": ErrorResponse}},
)
def get_products_by_category(
    category: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
    ctrl: ProductController = Depends(get_product_controller),
    _user_id: int = Depends(get_current_user_id),
):
    ''' Obter a lista de produtos filtrada por categoria com paginação. '''
    result = ctrl.get_products_by_category(category, skip=skip, limit=limit)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.put(
    "/{product_id}",
    response_model=ProductSingleResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_product(
    product_id: int,
    body: UpdateProductRequest,
    ctrl: ProductController = Depends(get_product_controller),
    _admin_id: int = Depends(get_current_admin_user_id),
):
    ''' Atualizar os dados de um produto específico. Apenas administradores podem atualizar produtos. '''
    result = ctrl.update_product(
        product_id,
        name=body.name,
        description=body.description,
        price=body.price,
        category=body.category,
        stock=body.stock,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_product(
    product_id: int,
    ctrl: ProductController = Depends(get_product_controller),
    _admin_id: int = Depends(get_current_admin_user_id),
):
    ''' Deletar um produto específico. Apenas administradores podem deletar produtos. '''
    existing = ctrl.get_product_by_id(product_id)
    if existing["status"] == "error":
        raise HTTPException(status_code=existing["code"], detail=existing["message"])
    result = ctrl.delete_product(product_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result
