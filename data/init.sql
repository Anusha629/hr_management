DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'employees') THEN
        CREATE TABLE employees (
          employee_id SERIAL PRIMARY KEY,
          last_name VARCHAR(255) NOT NULL,
          first_name VARCHAR(255) NOT NULL,
          email VARCHAR(255) NOT NULL,
          phone VARCHAR(50),
          designation_id INTEGER REFERENCES designation(designation_id) ON DELETE CASCADE,

        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leaves') THEN
        CREATE TABLE leaves (
       id SERIAL PRIMARY KEY,
       date DATE,
       employee INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
       reason VARCHAR(200),
       UNIQUE (employee, date)
       );
    END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'designation') THEN
      CREATE TABLE designation (
    designation_id SERIAL PRIMARY KEY,
    designation_name VARCHAR(100) NOT NULL,
    Percentage_of_employees INTEGER NOT NULL,
    Total_num_of_leaves INTEGER NOT NULL
);  
    END IF;
END $$;



