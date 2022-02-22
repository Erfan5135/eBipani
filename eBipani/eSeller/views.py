from django.shortcuts import render, redirect
from django.db import connection

# Create your views here.


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def check(request):
    if request.session.has_key('email'):
        mail = request.session['email']
        with connection.cursor() as c:
            role = c.callfunc("GET_ROLE", str, [mail])
        if role == 'SELLER':
            return True
        else:
            return False
    else:
        return False


def index(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')
    return render(request, 'sellerHome.html')


"""
profile(request)
input:
output: returns customer's details
"""


def profile(request):

    if check(request) is False:
        return redirect('/eApp/users/login/')

    data = {}
    username = request.session['email']
    password = ''

    try:
        with connection.cursor() as c:
            query = """ SELECT PASSWORD, PHONE, CITY, COUNTRY, POSTAL_CODE, SHOP_NAME, REGISTRATION_NO, BKASH_NO 
                        FROM USERS JOIN SELLER
                        ON USERS.EMAIL = SELLER.EMAIL
                        WHERE USERS.EMAIL = %s
                    """
            c.execute(query, [username])
            d = dictfetchall(c)

            data = {
                'sname': d[0]['SHOP_NAME'],
                'regi': d[0]['REGISTRATION_NO'],
                'phone': d[0]['PHONE'],
                'bkash': d[0]['BKASH_NO'],
                'city': d[0]['CITY'],
                'country': d[0]['COUNTRY'],
                'postalcode': d[0]['POSTAL_CODE']
            }
            password = d[0]['PASSWORD']
    except:
        pass

    try:
        if request.method == 'POST':
            sname = request.POST.get('sname')
            regi = request.POST.get('regi')
            phone = request.POST.get('phone')
            bkash = request.POST.get('bkash')
            city = request.POST.get('city')
            country = request.POST.get('country')
            postalcode = request.POST.get('postalcode')
            cpass = request.POST.get('cpass')
            npass = request.POST.get('npass')
            rnpass = request.POST.get('rnpass')
            msg = 'updated'

            if (len(cpass) != 0 and str(hash(cpass)) != password) or rnpass != npass:
                msg = 'please fill password fields correctly'
            elif (cpass == password and rnpass == npass):
                with connection.cursor() as c:
                    query = """ UPDATE USERS
                                SET PASSWORD = %s
                                WHERE EMAIL = %s
                            """
                    c.execute(query, [str(hash(npass)), username])
           
            with connection.cursor() as c:
                query = """ UPDATE SELLER
                            SET SHOP_NAME = %s,
                                REGISTRATION_NO = %s,
                                BKASH_NO = %s
                            WHERE EMAIL = %s
                        """
                c.execute(query, [sname, regi, bkash, username])

                query = """ UPDATE USERS
                            SET PHONE = %s,
                                CITY = %s,
                                COUNTRY = %s,
                                POSTAL_CODE = %s
                            WHERE EMAIL = %s
                        """
                c.execute(
                    query, [phone, city, country, postalcode, username])

            data = {
                'sname': sname,
                'regi': regi,
                'phone': phone,
                'bkash': bkash,
                'city': city,
                'country': country,
                'postalcode': postalcode,
                'msg': msg
            }

    except:
        pass
    return render(request, 'sellerProfile.html', data)


def allProducts(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    username = request.session['email']
    data = {}
    query = '''SELECT
                    PRODUCT_ID, CATEGORY_NAME, SUB_CATEGORY, PRODUCT_NAME, UNIT_PRICE, UNITS_IN_STOCK, UNITS_ON_ORDER, IMAGE, DESCRIPTION 
                FROM
                    "PRODUCT" 
                WHERE
                    SELLER_EMAIL = %s;'''
    with connection.cursor() as c:
        c.execute(query, [username])
        data = dictfetchall(c)
    return render(request, 'sellerProducts.html', {'data': data})


def addProducts(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    return render(request, 'sellerAddProducts.html')


def editProducts(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    d = {}
    data = {}
    if request.method == 'POST':
        id = request.POST.get('id')
    with connection.cursor() as c:
        query = """select * from product where product_id = %s"""
        c.execute(query, [id])
        d = dictfetchall(c)
        data['PRODUCT_ID'] = id
        data['CATEGORY_NAME'] = d[0]['CATEGORY_NAME']
        data['SUB_CATEGORY'] = d[0]['SUB_CATEGORY']
        data['PRODUCT_NAME'] = d[0]['PRODUCT_NAME']
        data['UNIT_PRICE'] = d[0]['UNIT_PRICE']
        data['UNITS_IN_STOCK'] = d[0]['UNITS_IN_STOCK']
        data['DESCRIPTION'] = d[0]['DESCRIPTION']
    return render(request, 'sellerEditProducts.html', {'data': data})


def sellerOrders(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    un = request.session['email']
    DATA = {}

    try:
        if request.method == 'GET' and 'approveBtn' in request.GET:
            oid = request.GET['oid']
            with connection.cursor() as c:
                query = """ SELECT POSTAL_CODE PC
                            FROM ORDER_DETAILS 
                            WHERE ORDER_ID = %s"""
                c.execute(query, [oid])
                pc = dictfetchall(c)
                pc = pc[0]['PC']
                query = """ UPDATE ORDER_DETAILS 
                            SET STATUS = 'APPROVED',
                                SHIPPER_ID = ( SELECT SHIPPER_ID FROM SHIPPER WHERE ABS( POSTAL_CODE - %s ) IN ( SELECT MIN( ABS( POSTAL_CODE - %s ) ) FROM SHIPPER ) ) 
                            WHERE
                                ORDER_ID = %s"""
                c.execute(query, [pc, pc, oid])
    except:
        pass

    try:
        query = """ SELECT TT.OID, TT.CE, GET_PRODUCT_NAME(TT.PID) NAME, TT.ODT, TT.PT, TT.DA, TT.PC, TT.TXN, TT.BKASH, TT.TP, S.TOTAL_UNIT
                    FROM (
                    SELECT OD.CUSTOMER_EMAIL CE, ORDERS.PRODUCT_ID PID, OD.ORDER_ID OID, OD.ORDER_DATE ODT, OD.PAYMENT_TYPE PT, OD.DELIVERY_ADDRESS DA, OD.POSTAL_CODE PC, OD.TRANSACTION_ID TXN, OD.BKASH_NO BKASH, OD.TOTAL_PRICE TP 
                    FROM ORDERS JOIN ORDER_DETAILS OD
                    ON 	ORDERS.ORDER_ID = OD.ORDER_ID AND 
                            UPPER(OD.STATUS)='PENDING' AND 
                            ORDERS.PRODUCT_ID IN (SELECT PRODUCT_ID FROM PRODUCT WHERE SELLER_EMAIL=%s)
                    ) TT 
                    JOIN SELECTS S
                    ON TT.CE = S.CUSTOMER_EMAIL AND S.PRODUCT_ID = TT.PID AND UPPER( STATUS ) <> 'SELECTED' AND TT.OID = TO_NUMBER(S.STATUS)
                    ORDER BY TT.OID"""
        with connection.cursor() as c:
            c.execute(query, [un])
            tdata = dictfetchall(c)
            data = []
            if len(tdata) > 0:
                l = 0
                r = 1
                while r < len(tdata):
                    if tdata[r]['OID'] == tdata[r-1]['OID']:
                        r += 1
                    else:
                        data.append(tdata[l:r])
                        l = r
                        r += 1
                data.append(tdata[l:r])
                DATA['data'] = data

    except:
        pass
    return render(request, 'sellerorders.html', DATA)


def addProductfunc(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    data = {}
    if request.method == 'POST':
        catagory = request.POST.get('catagory')
        subcatagory = request.POST.get('subcatagory')
        pname = request.POST.get('pName')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        email = request.session['email']

    with connection.cursor() as c:
        query = """select * from category where category_name = %s"""
        c.execute(query, [catagory])
        d = dictfetchall(c)
        if len(d) == 0:
            query = """insert into category(category_name) values(%s)"""
            c.execute(query, [catagory])
        query = """insert into product(category_name,sub_category,product_name,unit_price,units_in_stock,description,seller_email)
                     values(%s,%s,%s,%s,%s,%s,%s)"""
        c.execute(query, [catagory, subcatagory, pname,
                  price, stock, description, email])
        data['msg'] = 'Product Successfully Added'
    return render(request, "sellerAddProducts.html", {'data': data})


def editProductFunc(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    data = {}
    if request.method == 'POST':
        id = request.POST.get('id')
        catagory = request.POST.get('catagory')
        subcatagory = request.POST.get('subcatagory')
        pname = request.POST.get('pName')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        email = request.session['email']

    with connection.cursor() as c:
        query = """update product set category_name = %s,sub_category=%s,product_name=%s,unit_price=%s,
                    units_in_stock=%s,description=%s where product_id=%s"""
        c.execute(query, [catagory, subcatagory, pname,
                  price, stock, description, id])
        data['msg'] = 'Product Successfully Updated'
        data['PRODUCT_ID'] = id
        data['CATEGORY_NAME'] = catagory
        data['SUB_CATEGORY'] = subcatagory
        data['PRODUCT_NAME'] = pname
        data['UNIT_PRICE'] = price
        data['UNITS_IN_STOCK'] = stock
        data['DESCRIPTION'] = description
    return render(request, "sellerEditProducts.html", {'data': data})
