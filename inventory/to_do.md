🔥 IMPORTANT: We will implement auto stock updates later

When product is sold:

Create a StockMovement record

Reduce product.current_stock

When stock is added manually:

Create StockMovement record

Increase product.current_stock

We will add this logic in:

Service Layer

Serializer Validation

Views or Signals

subcategories

(doing it later keeps things clean)