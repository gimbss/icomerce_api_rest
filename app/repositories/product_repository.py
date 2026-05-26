from app.models.product import Product
from app.models.order_item import OrderItem
from app.exceptions.product_exception import ProductHasOrdersError

class ProductRepository:
    def __init__(self, session):
        self.session = session

    def get_product_by_id(self, product_id: int):
        product = self.session.query(Product).filter(Product.id == product_id).first()
        return product

    def get_product_by_name(self, name: str):
        product = self.session.query(Product).filter(Product.name == name).first()
        return product
    
    def get_products_by_category(self, category: str, skip: int = 0, limit: int = 20):
        query = self.session.query(Product).filter(Product.category.ilike(f"%{category}%"))
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        return products, total
    
    def create_product(self, name: str, description: str, price: float, category: str, stock: int):
        new_product = Product(name=name, description=description, price=price, category=category, stock=stock)
        self.session.add(new_product)
        self.session.flush()
        return new_product
    
    def update_product(self, product_id: int, name: str = None, description: str = None, price: float = None, category: str = None, stock: int = None):
        product = self.get_product_by_id(product_id)
        if not product:
            return None
        
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if category is not None:
            product.category = category
        if stock is not None:
            product.stock = stock
        
        self.session.add(product)
        return product
    
    def list_products(self, skip: int = 0, limit: int = 20):
        total = self.session.query(Product).count()
        products = self.session.query(Product).offset(skip).limit(limit).all()
        return products, total

    def delete_product(self, product_id: int):
        product = self.get_product_by_id(product_id)
        if not product:
            return False

        has_orders = self.session.query(OrderItem).filter(
            OrderItem.product_id == product_id
        ).first()
        if has_orders:
            raise ProductHasOrdersError(product_id=product_id)

        self.session.delete(product)
        self.session.flush()
        return True
