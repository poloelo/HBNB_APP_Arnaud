# HBnB - Technical Design Document (Part 1)

## 1. Introduction

This document serves as the comprehensive technical blueprint for the **HBnB** project (a simplified AirBnB clone). It outlines the system architecture, design decisions, and data flows that will guide the implementation phases.

The purpose of this document is to:

- Define the high-level architecture (N-tier) to ensure separation of concerns.
- Detail the Business Logic layer, including entities and their relationships.
- Visualize the communication flow between layers via API calls.

This blueprint ensures a structured approach to development, facilitating maintainability and scalability.

---

## 2. High-Level Architecture

```mermaid
flowchart TB
    %% ===================
    %% Presentation Layer
    %% ===================
    subgraph P["Presentation Layer"]
        direction TB
        API["API / Endpoints\n(Controllers / Routes)\n- POST /users\n- POST /places\n- POST /reviews\n- GET /places"]
        SVC["Services\n(Request handling)"]
        API --> SVC
    end

    %% ===================
    %% Business Logic Layer
    %% ===================
    subgraph B["Business Logic Layer"]
        direction TB
        FACADE["HBnB Facade\n(Unified interface)\n- create_user()\n- create_place()\n- create_review()\n- get_places()"]
        MODELS["Domain Models\n(User, Place, Review, Amenity)\n+ Business Rules\n+ Validation"]
        FACADE --> MODELS
    end

    %% ===================
    %% Persistence Layer
    %% ===================
    subgraph D["Persistence Layer"]
        direction TB
        REPO["Repository (Interface)\n(Data access abstraction)\n- save()\n- findById()\n- findAll()\n- update()\n- delete()"]
        DB["Database\n(Persistent storage)"]
        REPO --> DB
    end

    %% ===================
    %% Layer Communication (Dependencies)
    %% ===================
    SVC -->|Calls Facade| FACADE
    MODELS -->|CRUD operations| REPO
```

The HBnB application is built on a **Layered Architecture** (3-tier) using the **Facade Design Pattern**. This structure ensures that each layer has a specific responsibility and interacts with others through well-defined interfaces.

### Package Diagram

![High-Level Package Diagram](all diagrams/Detailed Class Diagram for Business Logic Layer.png)

### Explanatory Notes

- **Presentation Layer:** The entry point for users via the `ServiceAPI`. It handles HTTP requests and responses but contains no business logic. It delegates all processing to the Business Logic Layer.
- **Business Logic Layer & Facade Pattern:** This is the core of the application. We utilize the **Facade Pattern** (`HBnBFacade`) to provide a simplified, unified interface to the Presentation Layer. The API doesn't need to know about the complex relationships between `User`, `Place`, or `Review`; it simply calls methods on the Facade.
- **Persistence Layer:** Responsible for data storage. The Business Layer communicates with the `DatabaseRepository` to save or retrieve objects, abstracting the underlying database technology (SQL, File Storage, etc.).

---

## 3. Business Logic Layer

The detailed class diagram represents the core entities of the application and their interrelationships. All entities inherit from a common `BaseModel` to ensure consistency in ID generation and timestamping.

### Class Diagram

```mermaid
classDiagram
    direction TB

    %% ===================
    %% Base class (shared attributes and methods)
    %% ===================
    class BaseModel {
        <<abstract>>
        -UUID id
        -DateTime created_at
        -DateTime updated_at
        #save() void
        #update() void
        #delete() void
        +to_dict() dict
    }

    %% ===================
    %% User, Place, Review, Amenity classes
    %% ====================
    class User {
        +String first_name
        +String last_name
        +String email
        -String password
        +Boolean is_admin
        +register() bool
        +authenticate() bool
        +add_place(title, description, price, latitude, longitude) bool
        +has_reserved(place) bool
        +add_review(text, rating) bool
        +add_amenity(name, description) bool
    }

    class Place {
        +String name
        +String title
        +String description
        +Float price
        -Float latitude
        -Float longitude
        +String owner_id
        +List~Amenity~ amenities
        +list_all() List~Place~
        +get_by_criteria(criteria) List~Place~
        -get_all_reservation() List
    }

    class Review {
        +String text
        +Int rating
        +String user_id
        +String place_id
        +list_by_place(place_id) List~Review~
    }

    class Amenity {
        +String name
        +String description
        +list_all() List~Amenity~
    }

    %% ===================
    %% Inheritance relationships
    %% ===================
    BaseModel <|-- User : inherits
    BaseModel <|-- Place : inherits
    BaseModel <|-- Review : inherits
    BaseModel <|-- Amenity : inherits

    %% ===================
    %% Associations
    %% ===================
    User "1" --> "0..*" Place : manages
    User "1" --> "0..*" Review : writes
    Place "0..*" --> "0..*" Amenity : offers
    Review "0..*" --> "1" Place : about
```

### Explanatory Notes

- **BaseModel:** The abstract parent class. It automatically manages the unique identifier (`UUID`) and timestamps (`created_at`, `updated_at`) for every entity, reducing code duplication.
- **User:** Represents the registered users. A user can own multiple `Places` (Host) and write multiple `Reviews` (Guest).
- **Place:** The central entity. It is linked to a `User` (owner) and can have many `Reviews`. It also has a many-to-many relationship with `Amenity` (e.g., WiFi, Pool).
- **Relationships:**
  - **Composition/Aggregation:** A Place _has_ Reviews.
  - **Association:** Users interact with Places by writing Reviews.

---

## 4. API Interaction Flow

The following sequence diagrams illustrate how the three layers interact to fulfill specific user requests.

### 4.1. User Registration

This flow demonstrates the creation of a new user, highlighting the validation logic within the Business Layer.

```mermaid
sequenceDiagram
    %% Layers:
    %% Presentation: User, API
    %% Business Logic: Facade, BusinessLogic, Repository
    %% Persistence: Database

    actor User
    participant API as API (Presentation Layer)
    participant Facade as Facade
    participant BusinessLogic as Business Logic
    participant Repository as Repository (Interface)
    participant Database as Database

    User ->> API: POST /users with data
    API ->> Facade: create_user(data)

    alt "Missing required fields"
        Facade -->> API: 400 Bad Request - Missing fields
        API -->> User: Please fill all required fields
    else "Invalid email format"
        Facade -->> API: 400 Bad Request - Invalid email
        API -->> User: Invalid email address
    else "Password too short"
        Facade -->> API: 400 Bad Request - Weak password
        API -->> User: Password must be at least 8 characters
    else "Email already exists"
        Facade -->> API: 409 Conflict - Email already registered
        API -->> User: Email already in use
    else "Valid data"
        Facade ->> BusinessLogic: create_user_instance(data)
        BusinessLogic --> BusinessLogic: User(user_data)
        BusinessLogic ->> Repository: save(user)
        Repository ->> Database: INSERT user
        alt "Database error"
            Database -->> Repository: 500 Internal Server Error
            Repository -->> BusinessLogic: Persistence failed
            BusinessLogic -->> Facade: 500 Internal Server Error
            Facade -->> API: 500 Internal Server Error
            API -->> User: An error occurred, please try again
        else "Success"
            Database -->> Repository: OK + user_id
            Repository -->> BusinessLogic: User saved + user_id
            BusinessLogic -->> Facade: return user + user_id
            Facade -->> API: 201 Created + user object
            API -->> User: Success + user_id
        end
    end
```

- **Note:** The API handles the request format, but the `HBnBFacade` enforces rules (e.g., unique email) and security (password hashing) before asking the Persistence layer to save.

### 4.2. Creating a Place

This flow shows how a logged-in user creates a listing.

```mermaid
sequenceDiagram
    %% Layers:
    %% Presentation: User, API
    %% Business Logic: Facade, PlaceLogic, Repository
    %% Persistence: Database

    actor User
    participant API as API (Presentation Layer)
    participant Facade as Facade
    participant PlaceLogic as Business Logic
    participant Repository as Repository (Interface)
    participant Database as Database

    User ->> API: POST /places with place data
    API ->> Facade: create_place(data)

    alt Missing required fields
        Facade -->> API: 400 - Missing required fields
        API -->> User: Fill all required fields
    else Invalid price or location
        Facade -->> API: 400 - Invalid price/location
        API -->> User: Check your data
    else Invalid amenities
        Facade -->> API: 400 - Invalid amenities
        API -->> User: Provide valid amenities
    else Valid data
        Facade ->> PlaceLogic: validate and build place
        PlaceLogic --> PlaceLogic: Place(place_data)
        PlaceLogic ->> Repository: save(place_object)
        Repository ->> Database: INSERT place
        alt Database error
            Database -->> Repository: 500 Internal Server Error
            Repository -->> PlaceLogic: Persistence failed
            PlaceLogic -->> Facade: 500 Internal Server Error
            Facade -->> API: 500 Internal Server Error
            API -->> User: An error occurred, please try again
        else Success
            Database -->> Repository: OK + place_id
            Repository -->> PlaceLogic: Place saved + place_id
            PlaceLogic -->> Facade: Return place object
            Facade -->> API: 201 Created + place info
            API -->> User: Place successfully created
        end
    end
```

- **Note:** Authentication (JWT verification) usually happens at the API level (or middleware) to protect the Business Logic. The Facade then links the new Place to the authenticated Owner.

### 4.3. Review Submission

This flow illustrates the interaction involving multiple entities (User, Place, Review).

```mermaid
sequenceDiagram
    actor User
    participant API as API (Presentation)
    participant Facade as Facade
    participant Logic as Business Logic
    participant Repository as Repository (Interface)
    participant Database as Database

    User ->> API: POST /reviews with data
    API ->> Facade: create_review(data)

    alt Invalid input (missing or bad rating)
        Facade -->> API: 400 Bad Request
        API -->> User: Review data invalid
    else No reservation
        Facade ->> Logic: validate_reservation(user_id, place_id)
        Logic ->> Repository: check_reservation(user_id, place_id)
        Repository ->> Database: SELECT reservation
        Database -->> Repository: No match
        Repository -->> Logic: Forbidden
        Logic -->> Facade: 403 Forbidden
        Facade -->> API: Review not allowed
        API -->> User: Must reserve place first
    else Valid input + reserved
        Facade ->> Logic: create_review_instance(data)
        Logic --> Logic: Review(data)
        Logic ->> Repository: save(review)
        Repository ->> Database: INSERT review
        alt Database error
            Database -->> Repository: 500 Internal Server Error
            Repository -->> Logic: Persistence failed
            Logic -->> Facade: 500 Internal Server Error
            Facade -->> API: 500 Internal Server Error
            API -->> User: An error occurred, please try again
        else Success
            Database -->> Repository: OK + review_id
            Repository -->> Logic: Review saved + review_id
            Logic -->> Facade: review object (id, rating, text, date)
            Facade -->> API: 201 Created
            API -->> User: Review submitted
        end
    end
```

- **Note:** The Facade acts as the orchestrator. It ensures the `Place` exists and the data is valid before allowing the persistence of the `Review`.

### 4.4. Fetching a List of Places

This flow demonstrates how users search for available properties with optional filters.

```mermaid
sequenceDiagram
    actor User
    participant API as API (Presentation)
    participant Facade as Facade
    participant BusinessLogic as Business Logic
    participant Repository as Repository (Interface)
    participant Database as Database

    User->>API: GET /api/v1/places?filters

    alt Invalid parameters
        API-->>User: 400 Bad Request
    else Authentication/Authorization error
        API-->>User: 401 Unauthorized / 403 Forbidden
    else Valid request
        API->>Facade: get_places(filters)
        Facade->>BusinessLogic: get_places(filters)
        BusinessLogic->>Repository: find_places(query)
        Repository->>Database: SELECT * FROM places WHERE ...

        alt Database error
            Database-->>Repository: SQL Error
            Repository-->>BusinessLogic: Technical error
            BusinessLogic-->>Facade: Technical error
            Facade-->>API: Technical error
            API-->>User: 500 Internal Server Error
        else No results found
            Database-->>Repository: Empty ResultSet
            Repository-->>BusinessLogic: Empty list
            BusinessLogic-->>Facade: PlaceCollectionDTO (empty list, metadata)
            Facade-->>API: PlaceCollectionDTO
            API-->>User: 200 OK (empty list)
        else Results found
            Database-->>Repository: ResultSet
            Repository-->>BusinessLogic: List of Place objects
            BusinessLogic-->>Facade: PlaceCollectionDTO (list, metadata)
            Facade-->>API: PlaceCollectionDTO
            API-->>User: 200 OK + places data
        end
    end
```

- **Note:** The Business Logic layer transforms filter parameters into database queries through the Repository interface. The system handles three scenarios: database errors (500), no results found (200 with empty list), and successful results (200 with data). The `PlaceCollectionDTO` encapsulates both the list of places and metadata (total count, pagination info, applied filters).

---

## 5. Conclusion

This technical document outlines a robust and modular architecture for HBnB. By strictly adhering to the **3-Layer Architecture** and the **Facade Pattern**, we ensure that:

1.  **Scalability:** Components can be updated or replaced (e.g., changing the database) with minimal impact on other layers.
2.  **Maintainability:** The clear separation of logic makes debugging and feature addition straightforward.
3.  **Consistency:** The centralized Business Logic layer guarantees that rules are applied uniformly across the application.

This design serves as the definitive reference for the implementation phase.
