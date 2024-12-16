from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here' # Necessary for the flash messages in our applciation


UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png','jpg', 'jpeg', 'gif' }
app.config['UPLOAD_FOLDER']= UPLOAD_FOLDER

def allowed_file(filename): # For some reasons there were some erors if the file isn't in one of the 4 allowed extension type.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db(): #I have initialized my database here
    conn =sqlite3.connect('database.db') # We have been told we are allowed to use sqlite, so we did.
    c =conn.cursor()
    
    # It shouldn't try to create the table over and over again.
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL UNIQUE,
                  location TEXT,
                  profile_image TEXT)''')

    # Inserted default user(myself) if no user is inserted before.
    user_count= c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count== 0:
        c.execute('''
                INSERT INTO users (name, email, location, profile_image) 
                VALUES (?, ?, ?, ?)
                ''', ('Selin Günes', 'selingunes@gmail.com', 'Istanbul', '/static/images/selin.png'))
    
    # Created the other tables if they were not created before
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE,
                  count INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ad_no TEXT NOT NULL UNIQUE,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  price REAL NOT NULL,
                  city TEXT NOT NULL,
                  category_id INTEGER,
                  image_url TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (category_id) REFERENCES categories (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  product_id INTEGER NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')

    #Checked if the categories exist
    existing_categories =c.execute('SELECT COUNT(*) FROM categories').fetchone()[0] 
    
    if existing_categories== 0: #These are the categories that came to my mind. We have assigned some random numbers next to it so it would look more professional
        categories = [
            ('Vehicles',1234),
            ('Electronics',876),
            ('Real Estate',543),
            ('Home & Garden',987),
            ('Fashion',654)
        ]
        c.executemany('INSERT INTO categories (name, count) VALUES (?, ?)', categories)
    
    #Inserted 10 sample products as we are told.
    product_count =c.execute('SELECT COUNT(*) FROM products').fetchone()[0] #Inserted if not inserted before
    if product_count ==0:
        current_date =datetime.now().strftime('%d %B %Y')
        sample_products =[
            ('AD001','Toyota Camry 2023', 'Excellent condition car in low mileage', 2500000, 'Lefke', 1, '/static/images/car1.jpg', current_date),
            ('AD002', 'iPhone 14 Pro', 'Almost brand new, sealed in a box',4999, 'izmir', 2,'/static/images/iphone_13_pro.jpg',current_date),
            ('AD003', 'An amazing apartment from the middle of the Trabzon', 'Ortahisar, 2 bed, 2 bath', 5000000, 'Trabzon', 3, '/static/images/apartment.jpg', current_date),
            ('AD004','Garden Set', 'An amazing outdoor furniture set, almost for free!!! ', 2799, 'Ankara', 4,'/static/images/garden1.jpg', current_date),
            ('AD005', 'Designer Watch', 'Not a watch but a luxury timepiece', 2999, 'Bursa', 5, '/static/images/watch1.jpg',current_date),
            ('AD006', 'Welder Watch', 'Luxury Watch', 1499, 'Istanbul', 5, '/static/images/watch2.jpg', current_date),
            ('AD007','Invicta Watch', 'A gentlemanly watch for gentlemenly man', 4499, 'Lefkosa', 5, '/static/images/watch3.jpg', current_date),
            ('AD008','Nasar Watch', 'Quality Watch', 3299, 'Antep', 5, '/static/images/watch4.jpg', current_date),
            ('AD009','Ford ', 'A Family Car', 1500000, 'İzmit', 1, '/static/images/car2.jpeg', current_date),
            ('AD010', 'Ford ', 'A Car For Good Times', 2500000, 'Mersin', 1,'/static/images/car3.jpeg', current_date),
        ]
        c.executemany('''INSERT INTO products 
                         (ad_no, title, description, price,city,category_id,image_url ,created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', sample_products)
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def home():
    conn =sqlite3.connect('database.db')
    conn.row_factory =sqlite3.Row #Here we can access columns by name
    c = conn.cursor()
    
    #Got the categories and products here.
    categories= c.execute('SELECT * FROM categories').fetchall()
    products= c.execute('''
        SELECT p.*,c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        ORDER BY p.created_at DESC
        LIMIT 6
    ''').fetchall()
    
    conn.close()
    return render_template('home.html',categories= categories,products= products) # Send what we got to the home.html for rendering

@app.route('/search')
def search():
    query =request.args.get('q', '')
    conn =sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c =conn.cursor()
    
    products= c.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.title LIKE ? OR p.description LIKE ? OR p.city LIKE ?
    ''',(f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    
    categories= c.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    return render_template('search.html', products=products, query=query, categories=categories) # Got the search results back

@app.route('/listing/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    product = c.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE p.id = ?
    ''', (product_id,)).fetchone()
    
    if product is None:
        conn.close()
        return render_template('404.html'), 404
        
    conn.close()
    return render_template('detail.html', product=product)

@app.route('/api/categories/counts')
def get_category_counts():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    counts = {}
    results = c.execute('''
        SELECT c.id, COUNT(p.id) as count 
        FROM categories c 
        LEFT JOIN products p ON c.id = p.category_id 
        GROUP BY c.id
    ''').fetchall()
    
    for category_id, count in results:
        counts[category_id] = count
    
    conn.close()
    return jsonify(counts)

@app.route('/my_profile')
def my_profile():
    user_id = 1 

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch user info
    user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Fetch user's listings
    listings = c.execute('''
        SELECT p.* 
        FROM products p
        JOIN user_posts up ON p.id = up.product_id
        WHERE up.user_id = ?
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('my_profile.html', user=user, listings=listings)

@app.route('/category/<int:category_id>')
def category(category_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    category = c.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    products = c.execute('''
        SELECT p.*, c.name as category_name 
        FROM products p 
        JOIN categories c ON p.category_id = c.id 
        WHERE c.id = ?
    ''', (category_id,)).fetchall()
    
    categories = c.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    return render_template('category.html', category=category, products=products, categories=categories)

@app.route('/post-ad', methods=['GET', 'POST'])
def post_ad(): #If we wish to post a new add this route gets executed.
    if request.method== 'POST': #If the request method is post we get the title, description etc and 
        title= request.form['title'] 
        description= request.form['description']
        price= float(request.form['price'])
        city= request.form['city']
        category_id= int(request.form['category_id'])
        
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename= secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url= f'/static/images/{filename}'
        
        conn= sqlite3.connect('database.db')
        c= conn.cursor()
        
        ad_no= f"AD{datetime.now().strftime('%Y%m%d%H%M%S')}" # Generated an unique ad no.
        
        # Inserted the added product to our database
        c.execute('''INSERT INTO products 
                    (ad_no, title, description, price, city, category_id, image_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (ad_no, title, description, price, city, category_id, 
                     image_url, datetime.now().strftime('%d %B %Y')))
        
        new_product_id = c.lastrowid # Got the ID of the new product.
        
        #Added entry to user_posts to link product to our user
        user_id=1  #For now we assume we are the only user (we don't have login register etc.)
        c.execute('INSERT INTO user_posts (user_id, product_id) VALUES (?, ?)', (user_id, new_product_id))
        conn.commit()
        conn.close()
        
        flash('Your ad has been posted successfully!') #Noted the user.
        return redirect(url_for('product_detail', product_id=new_product_id))  # Redirect to product detail page
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    categories = c.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    return render_template('post_ad.html', categories=categories)

@app.route('/delete-listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    user_id=1

    conn=sqlite3.connect('database.db')
    c=conn.cursor()

    # Deleted the selected post from the user.
    c.execute('''
        DELETE FROM user_posts 
        WHERE user_id = ? AND product_id = ?
    ''', (user_id, listing_id))

    #Delete the product itself from our databese
    c.execute('''
        DELETE FROM products 
        WHERE id = ?
    ''', (listing_id,))
    conn.commit()
    conn.close()

    flash('Listing deleted successfully!', 'success') #Notified our user
    return redirect(url_for('my_profile'))

@app.errorhandler(404) #If the user tries to go to non-existing url (such as my_proFELE) this will pop up.
def page_not_found(e):
    return render_template('404.html'), 404

   

if __name__ == '__main__':
    os.makedirs('static/images', exist_ok=True)
    init_db()
    app.run(debug=True)