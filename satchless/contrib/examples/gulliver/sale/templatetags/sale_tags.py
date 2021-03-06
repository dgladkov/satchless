from django.utils.datastructures import SortedDict
from django.conf import settings
from django.core.urlresolvers import reverse
from django import template

from satchless.product.models import Category, Product

from .. import query

register = template.Library()

@register.filter
def pre_discount_price_range(price_range_chain):
    handlers_names = settings.SATCHLESS_PRICING_HANDLERS
    index = handlers_names.index('sale.handler')
    min_price, max_price = price_range_chain[handlers_names[index-1]]
    return SortedDict((('min', min_price), ('max', max_price)))

@register.filter
def category_in_sale_url(category):
    path = list(category.get_ancestors()) + [category]
    path = [c.slug for c in path]
    category_slugs = '/'.join(path)
    return reverse('sale', args=(category_slugs,))

@register.filter
def subcategories_in_sale(category):
    ProductCategory = Product.categories.through
    discounted_products = ProductCategory.objects.filter(product__discount__isnull=False) \
                                                        .values_list('category_id', flat=True)
    all_subcategories = Category.objects.filter(lft__gt=category.lft, rght__lt=category.rght,
                                                tree_id=category.tree_id)
    subcategories = query.add_filtered_related_count(Category.tree, all_subcategories,
                                                  discounted_products, 'category', 'products_count',
                                                  cumulative=True)
    subcategories = filter(lambda cat: cat.products_count, subcategories)
    return subcategories

@register.filter
def product_in_category_tree_url(product, category=None):
    if not category:
        return product.get_url()

    category = Category.objects.filter(products=product, lft__gte=category.lft,
                                       rght__lte=category.rght)[0]
    return product.get_url(category=category)

@register.inclusion_tag("sale/snippets/price.html")
def discount_price(product):
    return {
        'product': product
    }

