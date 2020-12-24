from .models import Category

def add_variable_to_context(request):
    return{
        'categories_var': Category.objects.all()[0:8]
    }