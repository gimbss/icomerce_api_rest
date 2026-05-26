from fastapi import APIRouter, Depends, HTTPException, Query, status
from api.dependencies import get_order_controller, get_current_user_id, get_current_admin_user_id
from api.schemas import (
    CreateOrderRequest,
    OrderCreateResponse,
    OrderSingleResponse,
    OrdersListResponse,
    OrderDeleteResponse,
    UpdateOrderStatusRequest,
    ErrorResponse,
)
from app.controllers.order_controller import OrderController

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def create_order(
    body: CreateOrderRequest,
    ctrl: OrderController = Depends(get_order_controller),
    user_id: int = Depends(get_current_user_id),
):
    ''' Criar um novo pedido para o usuário autenticado, verificando se os produtos existem e se a quantidade solicitada está disponível. Retornar os detalhes do pedido criado. '''
    items_data = []
    for item in body.items:
        item_dict = item.model_dump(exclude_none=True)
        items_data.append(item_dict)
    result = ctrl.create_order(user_id=user_id, items=items_data)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.get(
    "/{order_id}",
    response_model=OrderSingleResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_order(
    order_id: int,
    ctrl: OrderController = Depends(get_order_controller),
    user_id: int = Depends(get_current_user_id),
):
    ''' Obter os detalhes de um pedido específico, verificando se o usuário autenticado é o proprietário do pedido. '''
    result = ctrl.get_order_by_id(order_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    if result["order"]["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")
    return result


@router.get(
    "/user/{user_id}",
    response_model=OrdersListResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def get_orders_by_user(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
    ctrl: OrderController = Depends(get_order_controller),
    auth_user_id: int = Depends(get_current_user_id),
):
    ''' Obter a lista de pedidos do usuário autenticado com paginação, verificando se o usuário autenticado é o mesmo que está sendo consultado. '''
    if user_id != auth_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view another user's orders")
    result = ctrl.get_orders_by_user_id(user_id, skip=skip, limit=limit)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.delete(
    "/{order_id}",
    response_model=OrderDeleteResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def delete_order(
    order_id: int,
    ctrl: OrderController = Depends(get_order_controller),
    user_id: int = Depends(get_current_user_id),
):
    ''' Deletar um pedido específico, verificando se o usuário autenticado é o proprietário do pedido. Restaurar o estoque dos produtos do pedido ao deletar. '''
    order_result = ctrl.get_order_by_id(order_id)
    if order_result["status"] == "error":
        raise HTTPException(status_code=order_result["code"], detail=order_result["message"])
    if order_result["order"]["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this order")
    result = ctrl.delete_order(order_id)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result


@router.patch(
    "/{order_id}/status",
    response_model=OrderSingleResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def update_order_status(
    order_id: int,
    body: UpdateOrderStatusRequest,
    ctrl: OrderController = Depends(get_order_controller),
    admin_user_id: int = Depends(get_current_admin_user_id),
):
    ''' Atualizar o status de um pedido. Apenas administradores podem alterar o status. Status válidos: pending, confirmed, shipped, delivered, cancelled. Ao cancelar, o estoque dos produtos é restaurado. '''
    result = ctrl.update_order_status(order_id, body.status)
    if result["status"] == "error":
        raise HTTPException(status_code=result["code"], detail=result["message"])
    return result
