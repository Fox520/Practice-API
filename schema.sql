create schema if not exists demo;
create table if not exists MEDIA(
	media_id SERIAL primary key,
	link VARCHAR(255)
);

create table if not exists seller(
	seller_id serial primary key,
	display_name varchar(255) not null
);

create table if not exists FEEDBACK(
	feedback_id serial primary key,
	rating smallint not null,
	review text,
	date_posted date default current_date,
	check (rating > 0 and rating < 6)
);

create table if not exists BUYER(
	buyer_id VARCHAR(1024) primary key
);

create table if not exists product(
	product_id serial primary key,
	seller_id integer not null references seller(seller_id) on delete cascade on update cascade,
	media_id integer not null references media(media_id) on delete cascade on update cascade,
	feedback_id integer not null references feedback(feedback_id) on delete cascade on update cascade
);
drop type if exists quality_category cascade;
CREATE type quality_category AS ENUM ('new', 'used', 'refurbished', 'pre-owned');
create table if not exists product_information(
	product_info_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	product_name varchar(150) not null,
	product_summary text,
	details text,
	category varchar(50) not null,
	quantity smallint not null,
	color varchar(10),
	price float8 not null,
	in_stock bool not null,
	free_shipping bool default false,
	quality_cat quality_category not null default 'new',
	previous_price float8,
	data_added date default current_date,
	check (price > 0),
	check (previous_price > 0),
	check (quantity > 0)
);

create table if not exists cart(
	cart_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	quantity smallint not null,
	check (quantity > 0)
);

create table if not exists orders(
	order_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	order_date date default current_date,
	shipping_address varchar(500)
);

create table if not exists order_detail(
	order_id integer not null references orders(order_id) on delete cascade on update cascade,
	buyer_id varchar(1024) not null references buyer(buyer_id) on delete cascade on update cascade,
	quantity smallint not null,
	tax float8 not null,
	discount_amount float8 default 0,
	charge_per_item float8 not null,
	total float8 not null,
	check (total > 0),
	check (charge_per_item > 0),
	check (discount_amount > -1),
	check (tax > -1),
	check (quantity > 0),
	CONSTRAINT order_buyer_pkey PRIMARY KEY (order_id, buyer_id)
);

create table if not exists CustomerQuestionsAndAnswers(
	qna_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	question varchar(250) not null,
	answer varchar(550),
	date_posted date default current_date
);

create table if not exists coupon (
	coupon_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	coupon_code varchar(20) not null,
	percent_reduction float8 not null
);
