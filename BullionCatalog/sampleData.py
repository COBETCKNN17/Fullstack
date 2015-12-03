# The original version of the script was provided by Udacity
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, User, Item

# Q: how do we make sure that we are not adding the same item in 
# the existing database? Do we use "unique" key in db rather than the followng?
# if os.path.isfile("catsupplies.db"):
# os.remove("catsupplies.db")
# print "existing db removed"

engine = create_engine('sqlite:///bullion.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


user1 = User(name="Felix", email = "felix.markman@cirruscpq.com")
session.add(user1)
session.commit()

Gold = Category(name="Gold")
session.add(Gold)

American_Eagle_Coin = Item(name="American Gold Eagle Coin",
                           category=Gold,
                           image="http://cdn.jmbullion.com/wp-content/uploads/2014/09/2015-AE-Gold-Bullion-O-2000.jpg",
                           description="1 troy oz of .999 pure Gold Coin",
                           mint="US Mint")
session.add(American_Eagle_Coin)
session.commit()

Canadian_Maple_Leaf = Item(name="Canadian Gold Maple Leaf Coin",
                           category=Gold,
                           image="http://cdn.jmbullion.com/wp-content/uploads/2013/12/2014-canadian-gold-maple-leaf-obverse.jpg",
                           description="1 troy oz of .9999 pure Gold Coin",
                           mint="Canadian Mint")
session.add(Canadian_Maple_Leaf)
session.commit()

Austrian_Philharmonic= Item(name="Austrian Gold Philharmonic Coin",
                            category=Gold,
                           image="http://store.royalmetalsgroup.com/content/images/thumbs/0000149_1oz_gold_austrian_philharmonic_random_dates.jpeg",
                           description="1 troy oz of .9999 pure Gold Coin",
                           mint="Austrian Mint")
session.add(Austrian_Philharmonic)
session.commit()

Austrian_Philharmonic= Item(name="Austrian Gold Philharmonic Coin",
                            category=Gold,
                           image="http://store.royalmetalsgroup.com/content/images/thumbs/0000149_1oz_gold_austrian_philharmonic_random_dates.jpeg",
                           description="1 troy oz of .9999 pure Gold Coin",
                           mint="Austrian Mint")
session.add(Austrian_Philharmonic)
session.commit()

South_African_Krugerrand = Item(name="South African Gold Krugerrand Coin",
                            category=Gold,
                            image="http://cdn.jmbullion.com/wp-content/uploads/2015/01/krugerrand-1ozgold-2015variant.jpg",
                            description="1 troy oz of .9167 pure Gold Coin",
                            mint="South African Mint")
session.add(South_African_Krugerrand)
session.commit()


#Silver
Silver = Category(name="Silver")
session.add(Silver)

Australian_Kookaburra = Item(name="Australian Silver Kookaburra Coin",
                             category=Silver,
                             image="http://cdn.jmbullion.com/wp-content/uploads/2014/08/SCKOOK115-reverse.jpg",
                             description="1 troy oz of pure .999 Silver Coin",
                             mint="Australian Mint")
session.add(Australian_Kookaburra)
session.commit()

Blue_Ridge_Parkway = Item(name="Blue Ridge Parkway Silver Coin",
                          category=Silver,
                          image="http://cdn.jmbullion.com/wp-content/uploads/2015/05/blue-ridge-parkway-atb.jpg",
                          description="1 troy oz of pure .999 oz Silver Coin with North Carolina Blue Ridge Parkway face",
                          mint="US Mint")
session.add(Blue_Ridge_Parkway)
session.commit()

Armenian_Noahs_Arc = Item(name="Armenian Silver Noah's Ark Coin",
                          category=Silver,
                          image="http://cdn.jmbullion.com/wp-content/uploads/2015/02/1-oz-noahs-2015.jpg",
                          description="1 troy oz of pure .999 oz Silver Coin from Armenia",
                          mint="Armenian Mint")
session.add(Armenian_Noahs_Arc)
session.commit()

Burundi_African_Lion = Item(name="Burundi Silver African Lion Coin",
                            category=Silver,
                             image="http://cdn.jmbullion.com/wp-content/uploads/2015/05/2015-burundi-africanlion-ngc-ms69.jpg",
                             description="1 troy oz of .999 pure Silver Coin from Africa",
                             mint="Burundi Mint")
session.add(Burundi_African_Lion)
session.commit()

New_Zealand_Taku = Item(name="New Zealand Silver Fiji Taku Coin",
                        category=Silver,
                        image="http://cdn.jmbullion.com/wp-content/uploads/2013/09/taku-rev.jpg",
                        description="1 oz of .999 pure Silver Coin with Turtle Face",
                        mint="New Zealand Mint")
session.add(New_Zealand_Taku)
session.commit()

#Platinum
Platinum = Category(name="Platinum")
session.add(Platinum)
session.commit()

Isle_of_Man_Noble = Item(name="Isle of Man Noble",
                         category=Platinum,
                         image="https://bullion.nwtmint.com/images/_productpages/rotator/platinum/isle_obv_rev.jpg",
                         description="1 oz of pure .9995 Platinum Coin with Ship Face",
                         mint="Mint of England")
session.add(Isle_of_Man_Noble)
session.commit()

Platinum_Koala = Item(name="Australian Platinum Koala",
                      category=Platinum,
                      image="https://bullion.nwtmint.com/images/_productpages/rotator/platinum/koala.jpg",
                      description="1 oz of pure .9995 Platinum Coin with Koala Face",
                      mint="Australian Mint")
session.add(Platinum_Koala)
session.commit()

American_Eagle_Platinum_Coin = Item(name="American Eagle Platinum Coin",
                        category=Platinum,
                        image="https://bullion.nwtmint.com/images/_productpages/rotator/platinum/eagle_obv_rev.jpg",
                        description="1 oz of pure .9995 American Platinum with Lady Liberty face",
                        mint="US Mint")
session.add(American_Eagle_Platinum_Coin)
session.commit()

Canadian_Maple_Leaf_Platinum = Item(name="Canadian Maple Leaf Platinum",
                        category=Platinum,
                        image="https://bullion.nwtmint.com/images/_productpages/rotator/platinum/maple_obv_rev.jpg",
                        description="1 oz of pure .9995 Canadian Platinum with Maple Leaf face",
                        mint="Canadian Mint")
session.add(Canadian_Maple_Leaf_Platinum)
session.commit()

print 'items have been added'
