
### Internal SCIM User structure - and JSON/DB fields name ref. (json used in REST API)
##### from: `determined-ee/master/pkg/model/scim_user.go`
##### db implementation ref: `determined-ee/master/internal/db/postgres_scim.go` 

```
    ID         UUID       `db:"id" json:"id"`                           <<- mandatory
    Username   string     `db:"username" json:"userName"`               <<- mandatory 
    ExternalID string     `db:"external_id" json:"externalId"`
    Name       SCIMName   `db:"name" json:"name"`
    Emails     SCIMEmails `db:"emails" json:"emails"`
    Active     bool       `db:"active" json:"active"`

    PasswordHash null.String `db:"password_hash" json:"password_hash,omitempty"`

    Password string          `json:"password,omitempty"`
    Schemas  SCIMUserSchemas `json:"schemas"`                           -> const string
    Meta     *SCIMUserMeta   `json:"meta"`                  

    UserID        UserID                 `db:"user_id" json:"-"`
    RawAttributes map[string]interface{} `db:"raw_attributes" json:"-"`
```
Name field structure
```
    GivenName  string `json:"givenName"`
    FamilyName string `json:"familyName"`
```
Emails field structure 
```
    Type    string `json:"type"`
    SValue  string `json:"value"`
    Primary bool   `json:"primary"`
```
Meta field structure
```
    ResourceType SCIMUserResourceType `json:"resourceType"`
    Location     string               `json:"location"`
```
Password hash generation (golang)
```
    from determined-ee/master/pkg/model/scim_user.go 

    const clientSidePasswordSalt = "GubPEmmotfiK9TMD6Zdw" // #nosec G101

    // replicateClientSideSaltAndHash replicates the password salt and hash done on the client side.
    // We need this because we hash passwords on the client side, but when SCIM posts a user with
    // a password to password sync, it doesn't so when we try to log in later, we get a weird,
    // unrecognizable sha512 hash from the frontend.
    func replicateClientSideSaltAndHash(password string) string {
        sum := sha512.Sum512([]byte(clientSidePasswordSalt + password))
        return fmt.Sprintf("%x", sum)
    }
```
SCIM User list structure
```
    TotalResults int         `json:"totalResults"`
    StartIndex   int         `json:"startIndex"`
    Resources    []*SCIMUser `json:"Resources"`

    ItemsPerPage int             `json:"itemsPerPage"`
    Schemas      SCIMListSchemas `json:"schemas"`        -> const string
```
---
### Internal SCIM Group structure - and JSON/DB fields name ref. (json for REST API)
##### from: `determined-ee/master/pkg/model/scim_group.go` 
```
    ID          UUID        `json:"id"`
    DisplayName string      `json:"displayName"`
    Members     []*SCIMUser `json:"members"`

    Schemas SCIMGroupSchemas `json:"schemas"`
    Meta    *SCIMGroupMeta   `json:"meta"`
```
SCIM Group list structure
```
    TotalResults int          `json:"totalResults"`
    StartIndex   int          `json:"startIndex"`
    Resources    []*SCIMGroup `json:"Resources"`

    ItemsPerPage int             `json:"itemsPerPage"`
    Schemas      SCIMListSchemas `json:"schemas"`
```
---
### MLDE SCIM APIs Implementation
### from: determined-ee/master/internal/plugin/scim/service.go
```
<MLDE SCIM EP>/Users           GET    GetUsers    (gets the list of users)
<MLDE SCIM EP>/Users/:user_id  GET    GetUser     (reads user data)
<MLDE SCIM EP>/Users           POST   PostUser    (creates a new user)
<MLDE SCIM EP>/Users/:user_id  PUT    PutUser     (updates all fiels)
<MLDE SCIM EP>/Users/:user_id  PATCH  PatchUser   (updates specifc fields)

    PATCH op available: replace
    
    NOTE: updating sub-path is not supported

    Fields that can be updated:
        - active
        - emails
        - name
    
        Note: Set a user as active=false -> delete the current 
              active sessions for that user
    
    Example
        # From: determined-ee/e2e_tests/tests/test_scim.py
        # active <- false
        patch_req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "operations": [{"op": "replace", "value": {"active": False}}]
        }
        
        r = requests.patch(
            "<MLDE SCIM EP>/Users/{user_id}"),
            auth=(<SCIM_USERNAME>, <SCIM_PASSWORD>),
            json=patch_req
        )

<MLDE SCIM EP>/Groups            GET      GetGroups    (returns an empty block)
```

Authentication mechanism

* basic 
* oauth


Errors
```
* Not Found Error      404    wrong entity id or path    API: GetUserPutUser, PatchUser 
* Bad Request Error    400    error in parameter         API: GetUsers, PostUser, PutUser, PatchUser
* Conflict Error       409    entity already present     API: PostUser, PutUser
```

