.. _product-custom_models:

=============================
Writing custom Product models
=============================

Now we are going to create a simple model for your custom product. A module
discussed here is present in ``satchless.contrib.examples.parrot``, so you
may refer to the code there too.

Let's assume we sell different species of parrots which may be red, green or
blue and also alive or `dead`_.

.. _`dead`: http://www.youtube.com/watch?v=4vuW6tQ0218

First, we create an applicaton for our parrots. Just run ``django-admin.py
startapp parrot`` or create the necessary files manually. We will need these::

    parrot/
        __init__.py
        admin.py
        models.py
        forms.py
        listeners.py

The models
----------

Let's start with a model for the product, in ``models.py`` file.::

    from django.db import models
    from satchless.product.models import ProductAbstract, Variant

    class Parrot(ProductAbstract):
        latin_name = models.CharField(max_length=20)

        class Meta:
            app_label = 'product'


    class ParrotVariant(Variant):
        product = models.ForeignKey(Parrot, related_name='variants')
        COLOR_CHOICES = (('red', 'red'), ('green', 'green'), ('blue', 'blue'))
        color = models.CharField(max_length=10, choices=COLOR_CHOICES)
        looks_alive = models.BooleanField()

        def __unicode__(self):
            return u"%s %s %s" % (
                    'Alive' if self.looks_alive else 'Dead',
                    self.get_color_display(),
                    self.product.name)

        class Meta:
            app_label = 'product'
            unique_together = ('product', 'color', 'looks_alive')

Looks pretty simple, doesn't it? Notice the optional ``app_label`` meta
attribute, which will cause parrots to appear in *Products* admin group.

.. note::
    In Satchless we assume that variants refer to their products via
    ``product`` field and the back reference is named ``variants``. It is
    not enforced explicitly, but breaking this rule will cause a crash.

Now we are going to add ``admin.py`` file in order to enter some new product
instances into our shop::

    from django.contrib import admin
    from satchless.product.admin import ProductAdmin

    from . import models

    class ParrotVariantInline(admin.TabularInline):
        model = models.ParrotVariant

    class ParrotAdmin(ProductAdmin):
        inlines = [ParrotVariantInline]

    admin.site.register(models.Parrot, ParrotAdmin)

Having written that, you may proceed to the admin panel and enter some parrots
to the system. You will notice a standard inline form for managing the
variants at the bottom of each *Product/Parrot* screen.

The form
--------

With the above setup you may run a product catalog and list your variants. But
it is still not enough to run a shop. For that, you will need a
``VariantForm``.  Forms of this type are shown to customers, in order to choose
an available variant and use them in any way (e.g. put them into the cart).

Let's start with a form. We will use drop-down for available colors and a
checkbox to select alive or dead variant. The following class goes to the
``forms.py`` file::

    from django import forms
    from satchless.product.forms import BaseVariantForm
    from . import models

    class ParrotVariantForm(BaseVariantForm):
        color = forms.CharField(
                max_length=10,
                widget=forms.Select(choices=models.ParrotVariant.COLOR_CHOICES))
        looks_alive = forms.BooleanField(required=False)

        def _get_variant_queryset(self):
            return models.ParrotVariant.objects.filter(
                    product=self.product,
                    color=self.cleaned_data['color'],
                    looks_alive=self.cleaned_data.get('looks_alive', False))

        def clean(self):
            if not self._get_variant_queryset().exists():
                raise forms.ValidationError("Variant does not exist")
            return self.cleaned_data

        def get_variant(self):
            return self._get_variant_queryset().get()

The minimal API requirement is to provide ``get_variant()`` method which is
going to be called on a validated form instance. It should return a variant
corresponding with the form data.

The validation, as shown in ``clean()`` method, is up to you.

.. note::
    It is worth having a look at the base class in
    ``satchless.product.forms.BaseVariantForm``. The constructor accepts
    either ``product`` or ``variant`` keyword. If given a product, it leaves
    the form empty. With a variant given, it initializes the form with the
    attributes of the variant.

The bindings
------------

What's left, is to bind the form with the models. We cannot do it explicitly
in ``models.py`` file for two reasons:

    * It would create cycle import between ``models.py`` and ``forms.py`` - a
      good example of *chicken and egg problem*.
    * We need a hook for future customizations and it's good to keep it
      separated from the model.

For that reasons we will use a signal. You may already see an example in the
``satchless.cart`` application, which asks for variant forms in order to build
"add to cart" forms for displayed products.

The basic signal handling is straightforward and goes to ``listeners.py``
file::

    from satchless.product.signals import variant_formclass_for_product
    from . import forms
    from . import models

    def get_variantformclass(sender, instance, formclass, **kwargs):
        formclass.append(forms.ParrotVariantForm)

    variant_formclass_for_product.connect(get_variantformclass, sender=models.Parrot)

The only thing left is to bind the listener when the application is being
loaded. The simple way is just to add the following line to ``__init__.py``::

    import listeners

The result
----------

With the setup above and ``satchless.cart`` enabled you will be able to choose
parrots and put them into the cart.
