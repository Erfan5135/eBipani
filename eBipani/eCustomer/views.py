from django.shortcuts import redirect, render
from django.db import connection

# Create your views here.

def hash(a):
    hv = 0
    p = 47
    m = 1e9 + 9
    p_pow = 1
    for c in a:
        hv = (hv + ord(c) * p_pow) % m 
        p_pow = (p_pow * p) % m

    return int(hv)


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


"""
Check(request)
input : 
Output: True if a user is logged in as a customer, else False
"""


def check(request):
    if request.session.has_key('email'):
        mail = request.session['email']
        with connection.cursor() as c:
            role = c.callfunc("GET_ROLE", str, [mail])
        if role == 'CUSTOMER':
            return True
        else:
            return False
    else:
        return False


""" 
searchProduct(request) 
input: text in search box
output: product details, fully/partially matched with searched text
"""


def searchProduct(request):
    if check(request) is False:
        return redirect('/eApp/users/login/')

    DATA = {}

    if request.method == 'GET' and 'searchBtn' in request.GET:
        searched = request.GET.get('searchBox')
        arr = searched.split()
        arr.insert(0, searched)

        tdata = []
        for a in arr:
            a = '%' + a.upper() + '%'
            try:
                with connection.cursor() as c:
                    query = """ (SELECT	CATEGORY_NAME,	PRODUCT_ID,	PRODUCT_NAME,	UNIT_PRICE,	UNITS_IN_STOCK,	IMAGE,	DESCRIPTION 
                                FROM	PRODUCT
                                WHERE UPPER(PRODUCT_NAME) LIKE %s )
                                UNION
                                (SELECT	CATEGORY_NAME,	PRODUCT_ID,	PRODUCT_NAME,	UNIT_PRICE,	UNITS_IN_STOCK,	IMAGE,	DESCRIPTION 
                                FROM	PRODUCT
                                WHERE UPPER(CATEGORY_NAME) LIKE %s )
                                UNION
                                (SELECT	CATEGORY_NAME,	PRODUCT_ID,	PRODUCT_NAME,	UNIT_PRICE,	UNITS_IN_STOCK,	IMAGE,	DESCRIPTION 
                                FROM	PRODUCT
                                WHERE UPPER(SUB_CATEGORY) LIKE %s )
                            """
                    c.execute(query, [a, a, a])
                    td = dictfetchall(c)
                    if len(td) > 0:
                        tdata += td
            except:
                pass
        data = []
        [data.append(x) for x in tdata if x not in data]
        DATA['data'] = data

    return render(request, 'customerProductByCategory.html', DATA)


"""
index(request)
input:
output: returns top 5 products' details from each category in customerHome.html
"""


def index(request):

    if check(request) == False:
        return redirect('/eApp/users/login/')

    DATA = {}

    try:
        with connection.cursor() as c:
            query = """ WITH temp_table AS ( 
                        SELECT  PRODUCT_ID, CATEGORY_NAME, PRODUCT_NAME, IMAGE, 
                                row_number ( ) over ( partition BY CATEGORY_NAME ORDER BY UNIT_PRICE ) AS rn 
                        FROM PRODUCT ) 
                        SELECT PRODUCT_ID, CATEGORY_NAME, PRODUCT_NAME, IMAGE 
                        FROM temp_table 
                        WHERE rn <= 5
                    """
            c.execute(query)
            tdata = dictfetchall(c)
            data = []
            if len(tdata) > 0:
                l = 0
                r = 1
                while r < len(tdata):
                    if tdata[r]['CATEGORY_NAME'] == tdata[r-1]['CATEGORY_NAME']:
                        r += 1
                    else:
                        data.append(tdata[l:r])
                        l = r
                        r += 1
                data.append(tdata[l:r])
                DATA['data'] = data
    except:
        pass

    return render(request, 'customerHome.html', DATA)


"""
productByCategory(request, category)
input: category name
output: returns product details of the category
"""


def productByCategory(request, category):

    if check(request) == False:
        return redirect('/eApp/users/login/')

    DATA = {}

    with connection.cursor() as c:
        query = """ SELECT CATEGORY_NAME, PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE, UNITS_IN_STOCK, IMAGE, DESCRIPTION  
                    FROM PRODUCT 
                    WHERE CATEGORY_NAME = %s
                """
        c.execute(query, [category])
        data = dictfetchall(c)
        DATA['data'] = data

    return render(request, 'customerProductByCategory.html', DATA)


"""
individual product(request, category, pid)
input: category name, product id
output: returns the individual product's details
"""


def individualProduct(request, category, pid):

    if check(request) is False:
        return redirect('/eApp/users/login/')

    data = {}
    username = request.session['email']

    try:
        with connection.cursor() as c:
            query = """ SELECT PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE, UNITS_IN_STOCK, IMAGE, DESCRIPTION
                        FROM PRODUCT 
                        WHERE CATEGORY_NAME = %s
                        AND PRODUCT_ID = %s
                    """
            c.execute(query, [category, pid])
            prod = dictfetchall(c)
            data['prod'] = prod

            query = """ SELECT FIRST_NAME AS NAME, CUSTOMER_COMMENT AS REVIEW
                        FROM REVIEW JOIN CUSTOMER
                        ON REVIEW.CUSTOMER_EMAIL = CUSTOMER.EMAIL
                        WHERE REVIEW.PRODUCT_ID = %s AND LENGTH(REVIEW.CUSTOMER_COMMENT) > 0
                    """
            c.execute(query, [pid])
            reviews = dictfetchall(c)
            data['reviews'] = reviews

            query = """ SELECT COUNT(CUSTOMER_EMAIL) AS FLAG
                        FROM ORDERS
                        WHERE CUSTOMER_EMAIL=%s AND PRODUCT_ID=%s
                    """
            c.execute(query, [username, pid])
            flag = dictfetchall(c)
            data['flag'] = flag[0]['FLAG']

            query = """ SELECT RATING, CUSTOMER_COMMENT AS REVIEW
                        FROM REVIEW
                        WHERE CUSTOMER_EMAIL=%s AND PRODUCT_ID=%s
                    """
            c.execute(query, [username, pid])
            result = dictfetchall(c)
            if len(result) > 0:
                data['rating'] = result[0]['RATING']
                data['review'] = result[0]['REVIEW']
    except:
        pass

    try:
        if request.method == 'GET' and 'add2cart' in request.GET:
            with connection.cursor() as c:
                c.callproc('ADD_TO_CART', [pid, username])
    except:
        pass

    try:
        if request.method == 'POST' and 'ratingbtn' in request.POST:
            rating = int(request.POST.get('rating'))
            data['rating'] = rating
            with connection.cursor() as c:
                c.callproc('UPDATE_RATING_REVIEW', [
                           username, pid, 'rating', rating])
    except:
        pass

    try:
        if request.method == 'POST' and 'reviewbtn' in request.POST:
            review = request.POST.get('review')
            data['review'] = review
            with connection.cursor() as c:
                c.callproc('UPDATE_RATING_REVIEW', [
                           username, pid, 'review', review])
    except:
        pass

    return render(request, 'customerIndividualProduct.html', data)


"""
profile(request)
input:
output: returns customer's details
"""


def profile(request):

    if check(request) == False:
        return redirect('/eApp/users/login/')

    data = {}
    username = request.session['email']
    password = ''

    try:
        with connection.cursor() as c:
            query = """ SELECT PASSWORD, PHONE, CITY, COUNTRY, POSTAL_CODE, FIRST_NAME, SECOND_NAME 
                        FROM USERS JOIN CUSTOMER
                        ON USERS.EMAIL = CUSTOMER.EMAIL
                        WHERE USERS.EMAIL = %s
                    """
            c.execute(query, [username])
            d = dictfetchall(c)

            data = {
                'fname': d[0]['FIRST_NAME'],
                'lname': d[0]['SECOND_NAME'],
                'phone': d[0]['PHONE'],
                'city': d[0]['CITY'],
                'country': d[0]['COUNTRY'],
                'postalcode': d[0]['POSTAL_CODE']
            }
            password = d[0]['PASSWORD']
    except:
        pass

    try:
        if request.method == 'POST':
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            phone = request.POST.get('phone')
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
                query = """ UPDATE CUSTOMER
                            SET FIRST_NAME = %s,
                                SECOND_NAME = %s
                            WHERE EMAIL = %s
                        """
                c.execute(query, [fname, lname, username])

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
                'fname': fname,
                'lname': lname,
                'phone': phone,
                'city': city,
                'country': country,
                'postalcode': postalcode,
                'msg': msg
            }

    except:
        pass
    return render(request, 'customerProfile.html', data)


"""
myOrders(request)
input:
output: returns customer's pending orders
"""


def myOrders(request):

    if check(request) == False:
        return redirect('/eApp/users/login/')

    Data = {}
    username = request.session['email']

    try:
        with connection.cursor() as c:
            query = """ SELECT TT.OID, TT.OD, TT.DD, TT.SD, TT.DA || ', ' || TT.PC ADDRESS, TT.TXN, TT.BKASH, TT.COST, GET_PRODUCT_NAME(TT.PID) NAME, T3.TOTAL_UNIT
                        FROM
                        (   SELECT T1.ORDER_ID OID, T1.ORDER_DATE OD, T1.DELIVERY_DATE DD, T1.SHIPPED_DATE SD, T1.DELIVERY_ADDRESS DA, T1.POSTAL_CODE PC, T1.TRANSACTION_ID TXN, T1.BKASH_NO BKASH, T1.TOTAL_PRICE COST, T2.PRODUCT_ID PID
                            FROM
                        ( SELECT * FROM ORDER_DETAILS WHERE CUSTOMER_EMAIL = %s AND UPPER( STATUS ) = 'PENDING' ) T1
                        JOIN ( SELECT * FROM ORDERS WHERE CUSTOMER_EMAIL = %s ) T2 ON T1.ORDER_ID = T2.ORDER_ID 
                        ) TT
                        JOIN ( SELECT * FROM SELECTS WHERE CUSTOMER_EMAIL = %s AND UPPER( STATUS ) <> 'SELECTED' ) T3 
                        ON TT.OID = TO_NUMBER( T3.STATUS ) AND TT.PID = T3.PRODUCT_ID
                    """
            c.execute(query, [username, username, username])
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
                Data['data'] = data
            
            query = """ SELECT TT.OID, TT.OD, TT.DD, TT.SD, TT.DA || ', ' || TT.PC ADDRESS, TT.TXN, TT.BKASH, TT.COST, GET_PRODUCT_NAME(TT.PID) NAME, T3.TOTAL_UNIT
                        FROM
                        (   SELECT T1.ORDER_ID OID, T1.ORDER_DATE OD, T1.DELIVERY_DATE DD, T1.SHIPPED_DATE SD, T1.DELIVERY_ADDRESS DA, T1.POSTAL_CODE PC, T1.TRANSACTION_ID TXN, T1.BKASH_NO BKASH, T1.TOTAL_PRICE COST, T2.PRODUCT_ID PID
                            FROM
                        ( SELECT * FROM ORDER_DETAILS WHERE CUSTOMER_EMAIL = %s AND UPPER( STATUS ) = 'APPROVED' ) T1
                        JOIN ( SELECT * FROM ORDERS WHERE CUSTOMER_EMAIL = %s ) T2 ON T1.ORDER_ID = T2.ORDER_ID 
                        ) TT
                        JOIN ( SELECT * FROM SELECTS WHERE CUSTOMER_EMAIL = %s AND UPPER( STATUS ) <> 'SELECTED' ) T3 
                        ON TT.OID = TO_NUMBER( T3.STATUS ) AND TT.PID = T3.PRODUCT_ID
                    """
            c.execute(query, [username, username, username])
            tdata = dictfetchall(c)
            adata = []
            if len(tdata) > 0:
                l = 0
                r = 1
                while r < len(tdata):
                    if tdata[r]['OID'] == tdata[r-1]['OID']:
                        r += 1
                    else:
                        adata.append(tdata[l:r])
                        l = r
                        r += 1
                adata.append(tdata[l:r])
                Data['adata'] = adata
    except:
        pass
    return render(request, 'customerOrders.html', Data)


"""
preOrderDetails(request, pid)
input: pid
output: collects all the payment information of an order
"""


def preOrderDetails(request, pid):

    if check(request) == False:
        return redirect('/eApp/users/login/')

    username = request.session['email']

    se = ''
    try:
        with connection.cursor() as c:
            se = c.callfunc("GET_SELLER_EMAIL", str, [pid])
    except:
        pass

    data = {}
    cost = 0

    try:
        with connection.cursor() as c:
            query = """ WITH TT ( PID, CE, QUANTITY ) AS (
                            SELECT PRODUCT_ID, CUSTOMER_EMAIL, TOTAL_UNIT 
                            FROM SELECTS
                            WHERE   CUSTOMER_EMAIL = %s AND 
                                    UPPER( STATUS ) = 'SELECTED' AND 
                                    PRODUCT_ID IN ( SELECT PRODUCT_ID FROM PRODUCT WHERE SELLER_EMAIL = %s ) 
                            )
                            SELECT TT.PID, P.PRODUCT_NAME, TT.QUANTITY, P.UNIT_PRICE, TT.QUANTITY * P.UNIT_PRICE AS TOTAL_PRICE, TT.CE CE, P.SELLER_EMAIL SE, SELLER.BKASH_NO AS BKASH 
                            FROM PRODUCT P  JOIN TT ON P.PRODUCT_ID = TT.PID
                                            JOIN SELLER ON P.SELLER_EMAIL = SELLER.EMAIL;"""

            c.execute(query, [username, se])
            D = dictfetchall(c)

            data['D'] = D
            cost = 0
            for d in D:
                cost += float(d['TOTAL_PRICE'])
            data['cost'] = cost

    except:
        pass

    try:
        if request.method == 'GET' and 'cancelBtn' in request.GET:
            with connection.cursor() as c:
                c.callproc("REVERT_STOCK", [se, username])
            return redirect('/eApp/users/customer/')
    except:
        pass

    try:
        if request.method == 'POST' and 'cnfrmOrderBtn' in request.POST:
            address = request.POST.get('address')
            postalcode = request.POST.get('postal')
            cbkash = request.POST.get('bkash')
            txn = request.POST.get('txnid')

            query = """ INSERT INTO ORDER_DETAILS(ORDER_DATE, DELIVERY_DATE, SHIPPED_DATE, PAYMENT_TYPE, DELIVERY_ADDRESS, POSTAL_CODE, 
                                    CUSTOMER_EMAIL, TRANSACTION_ID, BKASH_NO, SHIPPER_ID, TOTAL_PRICE, STATUS)
                        VALUES(SYSDATE, SYSDATE+15, SYSDATE+3, 'BKASH', %s, %s, %s, %s, %s, 2, %s, 'PENDING')"""

            with connection.cursor() as c:
                c.callproc("SET_STATUS_IN_SELECTS", [se, username])
                c.execute(query, [address, postalcode,
                                  username, txn, cbkash, cost])
            return redirect('/eApp/users/customer/myorders/')
    except:
        pass

    return render(request, 'customerPreOrderDetails.html', data)


"""
cart(request)
input:
output: details about selected products
"""


def cart(request):

    if check(request) is False:
        return redirect('/eApp/users/login/')

    username = request.session['email']
    DATA = {}

    try:
        if request.method == 'POST' and 'save' in request.POST:
            q = request.POST.get('quantity')
            pid = request.POST.get('PID')
            with connection.cursor() as c:
                query = """ UPDATE SELECTS
                            SET TOTAL_UNIT = %s
                            WHERE PRODUCT_ID = %s AND CUSTOMER_EMAIL = %s AND UPPER(STATUS) = 'SELECTED';"""
                c.execute(query, [q, pid, username])
    except:
        pass

    try:
        if request.method == 'POST' and 'orderBtn' in request.POST:
            pid = request.POST.get('pid')
            se = ''
            with connection.cursor() as c:
                se = c.callfunc("GET_SELLER_EMAIL", str, [pid])
            with connection.cursor() as c:
                flag = c.callfunc("IN_STOCK", int, [se, username])
                if flag == 0:
                    url = '/eApp/users/customer/confirmOrder/' + pid + '/'
                    return redirect(url)
                else:
                    query = ''' SELECT PRODUCT_NAME PN
                                FROM PRODUCT
                                WHERE PRODUCT_ID = %s'''
                    with connection.cursor() as c:
                        c.execute(query, [flag])
                        x = dictfetchall(c)
                        DATA['msg'] = 'This amount of ' + \
                            x[0]['PN'] + ' is not in stock'
    except:
        pass

    try:
        if request.method == 'POST' and 'deleteBtn' in request.POST:
            pid = request.POST.get('PID')
            query = """ DELETE FROM SELECTS
                        WHERE PRODUCT_ID=%s AND CUSTOMER_EMAIL=%s AND UPPER(STATUS)='SELECTED';"""
            with connection.cursor() as c:
                c.execute(query, [pid, username])
    except:
        pass

    try:
        if request.method == 'POST' and 'deleteOrderBtn' in request.POST:
            pid = request.POST.get('pid')
            se = ''
            with connection.cursor() as c:
                se = c.callfunc("GET_SELLER_EMAIL", str, [pid])
            query = """ DELETE FROM	SELECTS 
                        WHERE CUSTOMER_EMAIL = %s AND 
                        UPPER( STATUS ) = 'SELECTED'AND 
                        PRODUCT_ID IN ( SELECT PRODUCT_ID FROM PRODUCT WHERE SELLER_EMAIL = %s);"""
            with connection.cursor() as c:
                c.execute(query, [username, se])

        query = """ SELECT P.SELLER_EMAIL SE, P.CATEGORY_NAME PCN, S.PRODUCT_ID PID, P.PRODUCT_NAME PN, TOTAL_UNIT TU
                    FROM SELECTS S JOIN PRODUCT P 
                    ON S.PRODUCT_ID = P.PRODUCT_ID
                    WHERE CUSTOMER_EMAIL=%s AND STATUS='SELECTED'
                    GROUP BY P.SELLER_EMAIL, P.CATEGORY_NAME, S.PRODUCT_ID, P.PRODUCT_NAME, S.TOTAL_UNIT
                    ORDER BY P.SELLER_EMAIL;"""
        with connection.cursor() as c:
            c.execute(query, [username])
            tdata = dictfetchall(c)
            data = []
            if len(tdata) > 0:
                l = 0
                r = 1
                while r < len(tdata):
                    if tdata[r]['SE'] == tdata[r-1]['SE']:
                        r += 1
                    else:
                        data.append(tdata[l:r])
                        l = r
                        r += 1
                data.append(tdata[l:r])
                DATA['data'] = data
    except:
        pass

    return render(request, 'customerCart.html', DATA)
