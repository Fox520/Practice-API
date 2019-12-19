--create schema if not exists demo;
create table if not exists MEDIA(
	media_id SERIAL primary key,
	info json not null
);

create table if not exists organisation(
	org_id serial primary key,
	organisation_name varchar(150) not null	
);

create table if not exists seller(
	seller_id serial primary key,
	org_id integer references organisation(org_id) on delete cascade on update cascade,
	email varchar(255) not null unique,
	password_hash varchar(512) not null,
	info json not null
);

create table if not exists FEEDBACK(
	feedback_id serial primary key,
	rating smallint not null,
	review text,
	date_posted date default current_date,
	check (rating > 0 and rating < 6)
);

create table if not exists product(
	product_id serial primary key,
	seller_id integer not null references seller(seller_id) on delete cascade on update cascade,
	media_id integer not null references media(media_id) on delete cascade on update cascade
);

create table if not exists PRODUCT_FEEDBACK_JUNCTION_TABLE(
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	feedback_id integer not null references feedback(feedback_id) on delete cascade on update cascade,
	CONSTRAINT product_feedback_pkey PRIMARY KEY (product_id, feedback_id)
);

create table if not exists BUYER(
	buyer_id VARCHAR(1024) primary key,
	info json
);

create table if not exists product_information(
	product_info_id serial primary key,
	product_id integer not null references product(product_id) on delete cascade on update cascade,
	info json
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
	info json,
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
