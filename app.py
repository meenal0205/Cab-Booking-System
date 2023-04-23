from flask import Flask, render_template, request, session, redirect
from flask_mysqldb import MySQL
import MySQLdb
app = Flask(__name__)

app.secret_key = 'meenal123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'cab_transportation_system'

mysql = MySQL(app)

db = MySQLdb.connect(host="localhost", user="root",
                     passwd="root", db="cab_transportation_system")
cursor = db.cursor()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        details = request.form
        username = details['username']
        password = details['password']
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM userlogin WHERE username = % s AND password = % s', (username, password))
        account = cursor.fetchone()
        id = account[6]
        if account != None and username == account[0] and password == account[1] and account[5] == 'admin':
            return redirect('admin')
        elif account != None and username == account[0] and password == account[1] and account[5] == 'customer':
            content = {
                'name': account[3],
                'userid': account[6]
            }
            return render_template('index.html', content=content)
        else:
            return('error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        details = request.form
        username = details['username']
        password = details['password']
        email = details['email']
        Name = details['name']
        phoneno = details['phoneno']
        cursor.execute('select * from userlogin ')
        l = len(cursor.fetchall())

        cursor.execute("INSERT INTO userlogin VALUES (%s,%s,%s,%s,%s,%s,%s);",
                       (username, password, email, Name, phoneno, "customer", l+1))
        db.commit()

        return render_template('home.html')

    return render_template("register.html")


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/availablecabs', methods=['GET', 'POST'])
def availablecabs():
    cursor.execute("select driver.driver_id,driver.driver_name,cab.vehicle_type,cab.car_plate_number,cab.availability_status  from driver,cab  where cab.cabId=driver.cab_id; ")
    account = cursor.fetchall()
    availabe_drivers = ()

    for i in account:
        if i[4] == 1:
            availabe_drivers = availabe_drivers+(i,)
    print(availabe_drivers)

    return render_template('cabavailable.html', content=availabe_drivers)


@app.route('/bookride/<driverID>', methods=['GET', 'POST'])
def bookride(driverID):
    print(driverID)
    cursor.execute(" select driver.driver_name , driver.mobile_no , driver.License_number,cab.vehicle_type,cab.car_plate_number from driver,cab where driver.driver_id=%s and driver.cab_id=cab.cabId;", (driverID))

    driver = cursor.fetchone()

    print(driver)
    cursor.execute("SELECT * FROM ROUTE_DETAILS;")
    routes = cursor.fetchall()

    source = set()
    destination = set()
    for i in routes:
        source.add(i[1])
    for i in routes:
        destination.add(i[2])
    routes = (source, destination)
    if request.method == "POST":
        details = request.form
        s = details['source']
        d = details['destination']
        cursor.execute(
            'SELECT * from route_details  WHERE source = % s AND destination = % s', (s, d))
        cost = cursor.fetchone()

        cost = cost[4]
        print(cost)

        msg = 'The driver will confirm the ride shortly please wait at the pick up point'
        content = {'cost': cost, 'driver': driver, 'msg': msg}

        cursor.execute('select curdate();')
        date = cursor.fetchone()[0]
        cursor.execute('select curtime();')
        time = cursor.fetchone()[0]

        print(cost)
        cursor.execute('insert into requests (source,destination,driver_id,date,time,vehicle_type,acceptence_status) values(%s,%s,%s,%s,%s,%s,%s)',
                       (s, d, driverID, date, time, content['driver'][3], '0'))
        db.commit()
        return render_template('booking.html', content=content)

    return render_template('bookride.html', content=routes)


@app.route('/driver', methods=['GET', "POST"])
def driver():
    if request.method == "POST":
        form = request.form
        name = form['name']
        id = form['id']
        cursor.execute(
            'SELECT * FROM driver WHERE driver_name = % s AND driver_id = % s', (name, id))
        driver = cursor.fetchone()
        if driver == None:
            return("enter valid id and name")
        else:
            cursor.execute('select * from requests where driver_id=%s', (id))
            a = cursor.fetchone()
            content = {'a': a}

            return render_template('driverconfirm.html', content=content)

    return render_template('driver.html')


@app.route('/confirmed/<driverID>')
def confirmed(driverID):
    cursor.execute(
        "update requests set acceptence_status =%s where driver_id=%s;", ('1', driverID))
    db.commit()

    cursor.execute('select * from driver where driver_id=%s', (driverID,))
    cabid = cursor.fetchone()[4]

    print(cabid)
    cursor.execute(
        'update cab set availability_status=%s where cabID=%s;', ('0', cabid))
    db.commit()

    cursor.execute('select * from requests where driver_id=%s;', (driverID,))
    c = cursor.fetchone()
    source = c[1]
    destination = c[2]

    cursor.execute(
        'select * from route_details where source=%s and destination=%s', (source, destination))
    cost = cursor.fetchone()
    cost = cost[4]

    content = {
        'cost': cost,
        'source': source,
        'destination': destination,
        'driverId': driverID
    }

    return render_template('bill.html', content=content)


@app.route('/passengerdroped/<driverID>')
def passengerdroped(driverID):
    print(driverID)
    cursor.execute('select * from driver where driver_id=%s', (driverID,))
    cabid = cursor.fetchone()[4]

    print(cabid)
    cursor.execute(
        'update cab set availability_status=%s where cabID=%s;', ('1', cabid))
    db.commit()

    return redirect('/driver')


@app.route('/admin',)
def admin():

    return render_template('admin.html')


@app.route('/driverdetails')
def driverDetails():
    cursor.execute("select * from driver; ")
    drivers = cursor.fetchall()
    return render_template('driverdetails.html', content=drivers)


@app.route('/updateDriver/<driverID>', methods=["POST", "GET"])
def updateDriver(driverID):

    cursor.execute('select * from driver where driver_id=%s', (driverID,))
    details = cursor.fetchone()
    content = {
        'details': details
    }
    if request.method == "POST":
        form = request.form
        name = form['name']
        license = form['licence']

        mobile = form['mobileno']
        location = form['location']
        print(name, license, mobile, location)
        cursor.execute('update driver set driver_name=%s , mobile_no=%s ,  License_number=%s , location=%s',
                       (name, mobile, license, location))
        db.commit()
        return redirect('/driverDetails')

    return render_template('updateDriver.html', content=content)


@app.route('/addDriver', methods=["POST", "GET"])
def addDriver():
    if request.method == "POST":
        form = request.form

        name = form['Name']
        license = form['LicenseNumber']
        Mobile = form['Mobileno']
        location = form['location']
        cabid = form['Cabid']
        cursor.execute('insert into driver (License_number,mobile_no,Driver_name,cab_id,location) values(%s,%s,%s,%s,%s)',
                       (license, Mobile, name, cabid, location))
        db.commit()
        return redirect('/driverDetails')
    return render_template('addDriver.html')


@app.route('/cabdetails')
def cabdetails():
    cursor.execute('select * from cab')
    cabdetails = cursor.fetchall()

    return render_template('cabdetails.html', content=cabdetails)


@app.route('/updatecab/<cabID>', methods=['POST', 'GET'])
def updatecab(cabID):
    cursor.execute('select * from cab where cabid=%s', (cabID))
    details = cursor.fetchone()
    content = {
        'details': details
    }

    if request.method == 'POST':
        form = request.form
        vehicletype = form['vehicletype']
        car_plate_number = form['carplatenumber']
        cursor.execute('update cab set  vehicle_type=%s, car_plate_number=%s',
                       (vehicletype, car_plate_number))
        db.commit()

    return render_template('updatecab.html', content=content)


@app.route('/addcab',methods=["POST",'GET'])
def addcab():
    if request.method=='POST':
        
    
    return render_template('addcab.html')


if __name__ == '__main__':
    app.run(debug=True)
